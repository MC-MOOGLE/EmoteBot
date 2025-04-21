import os
import telebot
from telebot import types

from src.database.database import SessionLocal
from src.database.models import User, Settings
from src.database.services import save_image, get_users, find_similar_images
from src.emote_processor.get_emote import get_emotions
from src.emote_processor.create_calendar import create_calendar

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from dotenv import load_dotenv
from os import environ

load_dotenv()
TOKEN = environ.get("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Инициализация планировщика
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
    
    welcome_text = "Добро пожаловать! Выберите действие:"
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
        emotion = get_emotions(temp_path)
        msg = bot.send_message(message.chat.id, 
                              f"Распознанная эмоция: {emotion}",
                              reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, confirm_emotion, temp_path, emotion)
    else:
        msg = bot.send_message(message.chat.id, 
                              "Выберите эмоцию:",
                              reply_markup=emotion_keyboard())
        bot.register_next_step_handler(msg, save_emotion, temp_path)

def confirm_emotion(message, temp_path, detected_emotion):
    if message.text.lower() == 'подтвердить':
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
        bot.send_message(message.chat.id, "Неверная эмоция, попробуйте снова")

def save_photo(message, image_path, emotion):
    with SessionLocal() as session:
        user = session.query(User).get(str(message.chat.id))
    
        # Сохраняем в БД
        image_uuid = save_image(image_path, emotion, user.user_id)
        
        # Статистика
        total_users = get_users()
        emotion_users = get_users(emotion)
        
        bot.send_message(message.chat.id,
                        f"Картинка успешно сохранена! {total_users} других пользователя тоже загрузили селфи!\n"
                        f"У {emotion_users} пользователей такое же настроение!",
                        reply_markup=main_keyboard())
        
        # os.remove(image_path)

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
            # Берем последнее изображение
            last_image = sorted(user.images, key=lambda x: x.created_date, reverse=True)[0]
            similar = find_similar_images(last_image)
            
            if not similar:
                bot.send_message(message.chat.id, "Похожих пользователей не найдено")
            else:
                response = "Похожие пользователи:\n" + "\n".join([f"- {u['user_id']}" for u in similar])
                bot.send_message(message.chat.id, response)


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

# Запуск бота
if __name__ == "__main__":
    schedule_reminders()
    print("Bot ready")
    bot.polling(none_stop=True)