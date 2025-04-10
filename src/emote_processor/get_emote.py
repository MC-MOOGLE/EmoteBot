import cv2
from deepface import DeepFace

def get_emote(image_path: str):
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
        analysis = DeepFace.analyze(image_path, actions=['emotion'], silent=True)

        print(type(analysis), analysis)

        if not analysis or not isinstance(analysis, list):
            raise ValueError("No face detected or unable to recognize emotion in the image.")

        if len(analysis) > 1:
            raise ValueError("Multiple faces detected")

        result = analysis[0]
        
        dominant_emotion = result['dominant_emotion']
        print(f"Dominant emotion: {dominant_emotion}")
        return dominant_emotion
    except FileNotFoundError:
        raise FileNotFoundError
    
    return None

if __name__ == "__main__":
    get_emote("test_images/sad_1.jpg")