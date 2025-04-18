from datasets import load_dataset
from PIL import Image
import io

dataset = load_dataset('dataset')
for i, example in enumerate(dataset['train']):
    image_bytes = example['image']['bytes']
    image = Image.open(io.BytesIO(image_bytes))
    image.save(f"celeb_images/{i}.png")
