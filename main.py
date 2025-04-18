import os
import time
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np

from src.database.database import init_db
from src.database.services import save_image
from src.database.services import find_similar_images
init_db()


def display_actor_images(found_images, name):
    """
    Display all images for an actor in a single row with 5px spacing between them.
    All images are resized to 768px height while maintaining aspect ratio.
    
    Args:
        found_images (tuple): Tuple of image file paths (0 < len(images) < 1000)
    """
    if not found_images:
        print("No images to display")
        return
    
    target_height = 768
    
    # Open all images, convert to RGB, and resize to target height
    images = []
    for img_path in found_images:
        img = Image.open(img_path).convert('RGB')
        # Calculate new width maintaining aspect ratio
        width_percent = (target_height / float(img.size[1]))
        new_width = int((float(img.size[0]) * float(width_percent)))
        img = img.resize((new_width, target_height), Image.Resampling.LANCZOS)
        images.append(img)
    
    # Calculate total width (sum of all image widths + spacing between them)
    spacing = 5
    total_width = sum(img.width for img in images) + spacing * (len(images) - 1)
    
    # Create a new blank image with white background
    combined = Image.new('RGB', (total_width, target_height), color=(255, 255, 255))
    
    # Paste each image with spacing
    x_offset = 0
    for img in images:
        combined.paste(img, (x_offset, 0))
        x_offset += img.width + spacing
    
    # Display the combined image
    plt.figure(figsize=(15, 8))  # Larger figure size for better visibility
    plt.imshow(combined)
    plt.axis('off')
    # plt.savefig(f'{name}.png')
    plt.show()

folders = ['actors']
def main():
    # image_list = []
    # for folder in folders:
    #     emotion_dir = os.path.join('test_images', folder)
    #     if not os.path.exists(emotion_dir):
    #         continue
    #     for img_name in os.listdir(emotion_dir):
    #         img_path = os.path.join(emotion_dir, img_name)
    #         if os.path.isfile(img_path):
    #             image_list.append((img_path, folder))

    success = total = 0
    start_time = time.time()

    # for file in image_list:
    #     image, emotion = file

    #     try:
    #         image_id = save_image(
    #             image,
    #             emotion,
    #             "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
    #         )

    #         print(image_id)
    #         success += 1
    #     except ValueError:
    #         print(f"No face for {image}")
        
    #     total += 1

    # for image in os.listdir('images'):
    #     image_id = image.replace(".jpg", "")
    #     similar = find_similar_images(image_id, find_n=300, same_emotion=False, ignore_original_user=False)
    #     success += 1

    actors = {"Emma Watson": "283c8bc4-7f46-4188-b605-0b5d059e911a", "Jack Black": "ab1d96da-1439-49de-911c-0913e287cb29", "Johnny Depp": "f653a0e4-95d9-480d-8e7d-e393920cbb1d", "Will Smith": "f2326fe3-e9de-48b4-b754-205d258f91a2"}
    for actor, image_id in actors.items():
        print(actor)
        similar = find_similar_images(image_id, find_n=100, same_emotion=False, ignore_original_user=False)
        result = (file["file_path"] for file in similar)
        display_actor_images(result, actor)
        print(*result, sep="\n")

    print(f"Time taken: {time.time() - start_time} seconds")
    print(f"Total images: {total} / {success} succeed")

if __name__ == "__main__":
    main()