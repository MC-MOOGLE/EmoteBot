import cv2
from deepface import DeepFace

def get_emotions(image_path: str, backend: str = 'retinaface'):
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

        analysis = DeepFace.analyze(
            img_path=img,
            actions=['emotion'],
            detector_backend=backend,
            enforce_detection=False,
            silent=True
        )

        emotes = analysis[0].get('emotion')
        if emotes:
            print(*(f"{key}: {int(value * 10) / 10}" for key, value in emotes.items()), sep=", ")

        if not analysis or not isinstance(analysis, list):
            raise ValueError("No face detected or unable to recognize emotion in the image.")

        if len(analysis) > 1:
            raise ValueError("Multiple faces detected")

        result = analysis[0]
        
        if result['face_confidence'] < 0.80:
            return None
        return result
        
    except FileNotFoundError:
        raise FileNotFoundError
    
    return None

if __name__ == "__main__":
    for image in ("angry_1", "angry_2", "happy_1", "happy_2", "sad_1", "sad_2"):
        print(f"======= {image} =========")
        for backend in ('opencv', 'ssd', 'mtcnn', 'retinaface'):
            result = get_emotions(f"test_images/{image}.jpg", backend)

            if not result:
                print(f"{backend}: no emotion detected\n")
                continue

            dominant_emotion = result['dominant_emotion']
            print(f"{backend}: {dominant_emotion}\n")