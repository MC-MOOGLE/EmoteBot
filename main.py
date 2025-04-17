import os

from src.database.database import init_db
from src.database.services import save_image
init_db()

emotions = ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']
def main():
    image_list = []
    for emotion in emotions:
        emotion_dir = os.path.join('test_images', emotion)
        if not os.path.exists(emotion_dir):
            continue
        for img_name in os.listdir(emotion_dir):
            img_path = os.path.join(emotion_dir, img_name)
            if os.path.isfile(img_path):
                image_list.append((img_path, emotion))

    for file in image_list:
        image, emotion = file

        try:
            image_id = save_image(
                image,
                emotion,
                "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
            )

            print(image_id)
        except ValueError:
            print(f"No face for {image}")

if __name__ == "__main__":
    main()