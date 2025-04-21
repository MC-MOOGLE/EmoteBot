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

folders = ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']
def main():
    for i in range(100):
        current_user = f"test_user{i}"
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

        success = total = 0
        start_time = time.time()

        random.shuffle(image_list)
        for file in image_list[:25]:
            image, emotion = file

            selected_date = datetime.now() - timedelta(days=success)

            try:
                image_id = save_image(
                    image,
                    emotion,
                    current_user,
                    selected_date
                )

                print(image_id)
                success += 1
            except ValueError:
                print(f"No face for {image}")
            
            total += 1

    # for image in os.listdir('images'):
    #     image_id = image.replace(".jpg", "")
    #     similar = find_similar_images(image_id, find_n=300, same_emotion=False, ignore_original_user=False)
    #     success += 1

    # actors = {"Emma Watson": "283c8bc4-7f46-4188-b605-0b5d059e911a", "Jack Black": "ab1d96da-1439-49de-911c-0913e287cb29", "Johnny Depp": "f653a0e4-95d9-480d-8e7d-e393920cbb1d", "Will Smith": "f2326fe3-e9de-48b4-b754-205d258f91a2"}
    # for actor, image_id in actors.items():
    #     print(actor)
    #     similar = find_similar_images(image_id, find_n=100, same_emotion=False, ignore_original_user=False)
    #     result = (file["file_path"] for file in similar)
    #     display_actor_images(result, actor)
    #     print(*result, sep="\n")

    print(f"Time taken: {time.time() - start_time} seconds")
    print(f"Total images: {total} / {success} succeed")

if __name__ == "__main__":
    pass
    main()