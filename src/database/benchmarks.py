import os
import time
from PIL import Image
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import random

from src.database.database import init_db, SessionLocal
from src.database.services import save_image, find_similar_images
from src.database.models import User, Settings
init_db()

folders = ['actors'] # ['celeb_images'] #['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']

def create_test_users_and_save_images(n_users: int = 50, n_images_per_user: int = 50):
    for i in range(n_users):
        current_user = f"test_user{i}"
        print(current_user)
        with SessionLocal() as session:
            user = session.query(User).filter(User.user_id == str(current_user)).first()
        
            if not user:
                user = User(user_id=str(current_user))
                session.add(user)
                session.commit()
                
                # Создаем настройки по умолчанию
                settings = Settings(user_id=user.user_id)
                session.add(settings)
                session.commit()

        image_list = []
        for folder in folders:
            emotion_dir = os.path.join('test_images', folder)
            if not os.path.exists(emotion_dir):
                continue
            for img_name in os.listdir(emotion_dir):
                img_path = os.path.join(emotion_dir, img_name)
                if os.path.isfile(img_path):
                    image_list.append((img_path, folder))

        for file in image_list[i * n_images_per_user:(i + 1) * n_images_per_user]:
            image, emotion = file

            selected_date = datetime.now() # - timedelta(days=total)

            try:
                image_id = save_image(
                    image,
                    emotion,
                    current_user,
                    selected_date
                )

                print(image_id)
            except ValueError:
                print(f"No face for {image}")

def benchmark_similar_images(find_n: int = 1, total_images: int = -1):
    ids = []
    for image in os.listdir('images'):
        image_id = image.replace(".jpg", "")
        ids.append(image_id)

    success = total = 0
    start_time = time.time()

    for id in ids[:total_images]:
        total += 1
        similar = find_similar_images(id, find_n=find_n)
        success += 1

    print(f"Time taken: {time.time() - start_time} seconds")
    print(f"Total images: {total} / {success} succeed")

if __name__ == "__main__":
    create_test_users_and_save_images(1, 100)
    # benchmark_similar_images(100)