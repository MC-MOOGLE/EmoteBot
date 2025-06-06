import cv2
from deepface import DeepFace

def resize_for_deepface(image, target_size=(152, 152), max_dimension=1024):
    """
    Resize an image while maintaining aspect ratio, optimized for DeepFace.
    
    Parameters:
    - image: Input image (numpy array or file path)
    - target_size: The desired face analysis size (default (152,152) for DeepFace)
    - max_dimension: Maximum dimension to prevent over-processing large images
    
    Returns:
    - Resized image as numpy array
    """
    
    if isinstance(image, str):
        image = cv2.imread(image)
        if image is None:
            raise ValueError(f"Could not read image from path: {image}")
    
    h, w = image.shape[:2]
    scale = min(target_size[0]/h, target_size[1]/w)

    if h > target_size[0] and w > target_size[1]:
        scale = max(target_size[0]/h, target_size[1]/w)
    
    max_scale = min(max_dimension/h, max_dimension/w)
    scale = min(scale, max_scale)
    new_h, new_w = int(h * scale), int(w * scale)
    
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return resized

def get_emotions(image_path: str, backend: str = 'opencv'):
    """Detect human emotion in an image.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        str: Dominant detected emotion or None if no human found
        
    Raises:
        FileNotFoundError: If image file doesn't exist
        ValueError: If image is corrupted
    """
    try:
        img = cv2.imread(image_path)
        resized_image = resize_for_deepface(img)

        analysis = DeepFace.analyze(
            img_path=resized_image,
            actions=['emotion'],
            detector_backend=backend,
            enforce_detection=False,
            silent=True
        )

        if not analysis or not isinstance(analysis, list):
            raise ValueError("No face detected or unable to recognize emotion in the image.")

        if len(analysis) > 1:
            raise ValueError("Multiple faces detected")

        result = analysis[0]
        
        if result['face_confidence'] < 0.80:
            raise ValueError("No face detected or unable to recognize emotion in the image.")
        
        return result['dominant_emotion']
        
    except FileNotFoundError:
        raise FileNotFoundError

if __name__ == "__main__":
    pass