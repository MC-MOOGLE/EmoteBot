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

        print(type(analysis), analysis)

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
    for backend in ('opencv', 'ssd', 'mtcnn', 'retinaface'):
        result = get_emotions("test_images/sad_1.jpg", backend)

        if not result:
            print(f"{backend}: no emotion detected")
            continue
        
        dominant_emotion = result['dominant_emotion']
        print(f"{backend}: {dominant_emotion}")