from PIL import Image
import matplotlib.pyplot as plt

def create_similar_image(found_images):
    """
    Display all images for an actor in a single row with 5px spacing between them.
    All images are resized to 768px height while maintaining aspect ratio.
    
    Args:
        found_images (tuple): Tuple of image file paths (0 < len(images) < 100) for perfomance
    """
    if not found_images:
        print("No images to display")
        return
    
    target_height = 512
    
    images = []
    for img_path in found_images:
        img = Image.open(img_path).convert('RGB')
        width_percent = (target_height / float(img.size[1]))
        new_width = int((float(img.size[0]) * float(width_percent)))
        img = img.resize((new_width, target_height), Image.Resampling.LANCZOS)
        images.append(img)
    
    spacing = 5
    total_width = sum(img.width for img in images) + spacing * (len(images) - 1)
    combined = Image.new('RGB', (total_width, target_height), color=(255, 255, 255))
    
    x_offset = 0
    for img in images:
        combined.paste(img, (x_offset, 0))
        x_offset += img.width + spacing
    
    return combined

if __name__ == "__main__":
    pass