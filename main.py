import os
import telebot
from telebot import types

from src.database.database import SessionLocal
from src.database.models import User, Settings
from src.database.services import save_image, get_users, find_similar_images
from src.emote_processor.get_emote import get_emotions
from src.emote_processor.create_calendar import create_calendar
from src.emote_processor.similar_people_plot import create_similar_image

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from datetime import datetime
from dotenv import load_dotenv
from os import environ

load_dotenv()
TOKEN = environ.get("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)

scheduler = BackgroundScheduler()
scheduler.start()

# Клавиатуры
def main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('📅 Скачать календарь')
    keyboard.add('👥 Похожие люди')
    keyboard.add('⚙️ Настройки')
    return keyboard

def emotion_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    emotions = ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']
    for emotion in emotions:
        keyboard.add(emotion)
    return keyboard

def confirm_emotion_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('✅ Подтвердить')
    keyboard.add('📋 Выбрать вручную')
    return keyboard

def settings_keyboard(user_id):
    with SessionLocal() as session:
        settings = session.query(Settings).filter(Settings.user_id == str(user_id)).first()
        
        keyboard = types.InlineKeyboardMarkup()
        
        ai_status = "ВКЛ" if settings.ai_enabled else "ВЫКЛ"
        keyboard.add(types.InlineKeyboardButton(
            f"ИИ распознавание: {ai_status}", 
            callback_data=f"toggle_ai")
        )
        
        reminder_time = settings.reminder_time.strftime("%H:%M")
        keyboard.add(types.InlineKeyboardButton(
            f"Время напоминания: {reminder_time}",
            callback_data=f"change_time")
        )

        search_status = "РАЗРЕШЕНО" if settings.search_allowed else "ЗАПРЕЩЕНО"
        keyboard.add(types.InlineKeyboardButton(
            f"Поиск в похожих: {search_status}", 
            callback_data=f"toggle_search")
        )
        
        return keyboard

# Обработчики команд
@bot.message_handler(commands=['start'])
def handle_start(message):
    with SessionLocal() as session:
        user = session.query(User).filter(User.user_id == str(message.chat.id)).first()
    
        if not user:
            user = User(user_id=str(message.chat.id))
            session.add(user)
            session.commit()
            
            # Создаем настройки по умолчанию
            settings = Settings(user_id=user.user_id)
            session.add(settings)
            session.commit()
    
    welcome_text = "Добро пожаловать! Отправьте селфи, либо выберите действие:"
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_keyboard())

# Обработчик изображений
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    with SessionLocal() as session:
        user = session.query(User).get(str(message.chat.id))
        settings = user.settings
    
    # Сохраняем фото
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    temp_path = f"temp/temp_{message.chat.id}.jpg"
    with open(temp_path, 'wb') as new_file:
        new_file.write(downloaded_file)
    
    # Определяем эмоцию
    if settings.ai_enabled:
        try:
            emotion = get_emotions(temp_path)
            msg = bot.send_message(message.chat.id, f"Распознанная эмоция: {emotion}", reply_markup=confirm_emotion_keyboard())
            bot.register_next_step_handler(msg, confirm_emotion, temp_path, emotion)
        except:        
            msg = bot.send_message(message.chat.id, "Не удалось распознать эмоцию, выберите ее вручную.", reply_markup=emotion_keyboard())
            bot.register_next_step_handler(msg, save_emotion, temp_path)
    else:
        msg = bot.send_message(message.chat.id, "Выберите эмоцию:", reply_markup=emotion_keyboard())
        bot.register_next_step_handler(msg, save_emotion, temp_path)

# Другое
def get_username_from_user_id(user_id):
    try:
        chat = bot.get_chat(user_id)
        return chat.username
    except Exception as e:
        print(f"Error fecching {user_id}: {e}")
        return user_id

def confirm_emotion(message, temp_path, detected_emotion):
    if message.text == '✅ Подтвердить':
        save_photo(message, temp_path, detected_emotion)
    else:
        msg = bot.send_message(message.chat.id, 
                             "Выберите правильную эмоцию:",
                             reply_markup=emotion_keyboard())
        bot.register_next_step_handler(msg, save_emotion, temp_path)

def save_emotion(message, temp_path):
    if message.text.lower() in ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']:
        save_photo(message, temp_path, message.text.lower())
    else:
        bot.send_message(message.chat.id, "Неверная эмоция", reply_markup=main_keyboard())
    return

def save_photo(message, image_path, emotion):
    with SessionLocal() as session:
        user = session.query(User).get(str(message.chat.id))

        try:
            image_uuid = save_image(image_path, emotion, user.user_id)
        except ValueError:
            bot.send_message(message.chat.id, "Невозможно распознать лицо", reply_markup=main_keyboard())
            return
        except Exception as e:
            bot.send_message(message.chat.id, "Не удалось сохранить картинку", reply_markup=main_keyboard())
            return
        
        total_users = get_users()
        emotion_users = get_users(emotion)
        
        bot.send_message(message.chat.id,
                        f"Картинка успешно сохранена! Сегодня {total_users} других пользователя тоже загрузили селфи!\n"
                        f"У {emotion_users} пользователей такое же настроение!",
                        reply_markup=main_keyboard())
        
        # os.remove(image_path)
    return

# Обработчики кнопок
@bot.message_handler(func=lambda m: m.text == '📅 Скачать календарь')
def handle_calendar(message):
    with SessionLocal() as session:
        user = session.query(User).get(str(message.chat.id))
    
        if not user.images:
            bot.send_message(message.chat.id, "Сначала отправьте свое селфи!")
        else:
            calendar = create_calendar(user.user_id)
            bot.send_photo(message.chat.id, calendar)

@bot.message_handler(func=lambda m: m.text == '👥 Похожие люди')
def handle_similar(message):
    with SessionLocal() as session:
        user = session.query(User).get(str(message.chat.id))
    
        if not user.images:
            bot.send_message(message.chat.id, "Сначала отправьте свое селфи!")
        else:
            last_image = sorted(user.images, key=lambda x: x.created_date, reverse=True)[0]
            similar = find_similar_images(last_image)
            image = create_similar_image((data["file_path"] for data in similar))
            
            if not similar:
                bot.send_message(message.chat.id, "Похожих пользователей не найдено")
            else:
                bot.send_photo(message.chat.id, image)
                response = "Похожие пользователи:\n" + "\n".join([f"- {get_username_from_user_id(u['user_id'])}" for u in similar])
                bot.send_message(message.chat.id, response)

@bot.message_handler(func=lambda m: m.text == '⚙️ Настройки')
def handle_settings(message):
    user_id = str(message.chat.id)
    bot.send_message(message.chat.id, "⚙️ Настройки:", reply_markup=settings_keyboard(user_id))

# Настройки
@bot.callback_query_handler(func=lambda call: call.data == ('toggle_ai'))
def toggle_ai(call):
    user_id = call.message.chat.id
    with SessionLocal() as session:
        settings = session.query(Settings).filter(Settings.user_id == str(user_id)).first()
        settings.ai_enabled = not settings.ai_enabled
        session.commit()
        
    bot.edit_message_reply_markup(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=settings_keyboard(user_id)
    )

@bot.callback_query_handler(func=lambda call: call.data == ('toggle_search'))
def toggle_search(call):
    user_id = call.message.chat.id
    with SessionLocal() as session:
        settings = session.query(Settings).filter(Settings.user_id == str(user_id)).first()
        settings.search_allowed = not settings.search_allowed
        session.commit()
        
    bot.edit_message_reply_markup(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=settings_keyboard(user_id)
    )

@bot.callback_query_handler(func=lambda call: call.data == ('change_time'))
def change_time(call):
    user_id = call.message.chat.id
    msg = bot.send_message(
        call.message.chat.id,
        "Введите новое время в формате ЧЧ:MM (например 21:30):"
    )
    bot.register_next_step_handler(msg, process_time_input, user_id)

def process_time_input(message, user_id):
    try:
        new_time = datetime.strptime(message.text, "%H:%M").time()
        with SessionLocal() as session:
            settings = session.query(Settings).filter(Settings.user_id == str(user_id)).first()
            settings.reminder_time = new_time
            session.commit()
            
        scheduler.remove_job(f"reminder_{user_id}")
        trigger = CronTrigger(hour=new_time.hour, minute=new_time.minute)
        scheduler.add_job(
            send_reminder,
            trigger=trigger,
            args=[user_id],
            id=f"reminder_{user_id}"
        )
        
        bot.send_message(
            message.chat.id,
            f"Время напоминания обновлено на {new_time.strftime('%H:%M')}",
            reply_markup=main_keyboard()
        )
        
    except ValueError:
        bot.send_message(
            message.chat.id,
            "❌ Неверный формат времени! Используйте ЧЧ:MM",
            reply_markup=main_keyboard()
        )

# Планировщик
def schedule_reminders():
    with SessionLocal() as session:
        users = session.query(User).all()
        
        for user in users:
            trigger = CronTrigger(
                hour=user.settings.reminder_time.hour,
                minute=user.settings.reminder_time.minute
            )

            scheduler.add_job(
                send_reminder,
                trigger=trigger,
                args=[user.user_id],
                id=f"reminder_{user.user_id}"
            )

def send_reminder(user_id):
    bot.send_message(user_id, 
                    "Пора отправить сегодняшнее селфи!",
                    reply_markup=main_keyboard())

# Запуск
if __name__ == "__main__":
    schedule_reminders()
    print("Bot ready")
    bot.polling(none_stop=True)