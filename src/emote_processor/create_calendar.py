from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import datetime
import calendar
from collections import defaultdict
from src.database.services import get_user_data

def create_calendar(user_id, year: int | None = None, month: int | None = None, output_path="calendar.png"):
    now = datetime.datetime.now()

    if not year:
        year = now.year
    if not month:
        month = now.month
    
    month_cal = calendar.monthcalendar(year, month)
    day_data = defaultdict(list)
    
    entries = get_user_data(user_id)
    for entry in entries:
        date = entry["created_at"]
        if date.year == year and date.month == month:
            day_data[date.day].append(entry)

    # Параметры изображения
    cell_size = 100
    padding = 5
    header_height = 40
    cols = 7
    rows = len(month_cal)
    
    # Рассчитываем размеры
    width = cols * cell_size + (cols-1)*padding
    height = header_height + rows * cell_size + (rows-1)*padding
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    
    # Шрифты
    font = ImageFont.truetype("arial.ttf", 20)
    header_font = ImageFont.truetype("arial.ttf", 30)
    
    # Заголовок
    header = f"{calendar.month_name[month]} {year}"

    bbox = draw.textbbox((0, 0), header, font=header_font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]

    draw.text(((width - w)//2, 10), header, font=header_font, fill="black")

    emotion_colors = {
        "happy": (255, 255, 0),
        "sad": (0, 0, 255),
        "angry": (255, 0, 0),
        "neutral": (200, 200, 200),
        "surprise": (255, 165, 0),
        "disgust": (0, 255, 0),
        "fear": (128, 0, 128),
    }

    # Обработка дней
    for week_num, week in enumerate(month_cal):
        for day_num, day in enumerate(week):
            if day == 0:
                continue
                
            # Координаты ячейки
            x = day_num * (cell_size + padding)
            y = header_height + week_num * (cell_size + padding)
            
            # Рамка дня
            draw.rectangle([x, y, x+cell_size, y+cell_size], outline="gray")
            
            # Добавляем записи
            entries = day_data.get(day, [])
            if entries:
                try:
                    entry = entries[0]
                    with Image.open(entry["image_path"]) as photo:
                        # Обрезка до квадрата
                        w, h = photo.size
                        size = min(w, h)
                        left = (w - size) // 2
                        top = (h - size) // 2
                        photo = photo.crop((left, top, left+size, top+size))
                        photo = photo.resize((cell_size, cell_size))
                        
                        # Наложение цвета
                        color = emotion_colors.get(entry["emotion"], (255,255,255))
                        overlay = Image.new("RGBA", photo.size, color + (64,))
                        photo = Image.alpha_composite(
                            photo.convert("RGBA"), 
                            overlay
                        ).convert("RGB")
                        
                        img.paste(photo, (x, y))
                except Exception as e:
                    print(f"Error processing image: {e}")
            
            # Текст с номером дня
            draw.text((x + 5, y + 5), str(day), font=font, fill="black")

    # img.save(output_path)
    return img

if __name__ == "__main__":
    pass