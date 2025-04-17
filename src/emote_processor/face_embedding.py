import face_recognition

def get_face_embedding(image_path: str) -> list:
    image = face_recognition.load_image_file(image_path)
    face_locations = face_recognition.face_locations(image)
    
    if not face_locations:
        raise ValueError("No face detected in the image")
    
    face_encodings = face_recognition.face_encodings(
        image, 
        known_face_locations=[face_locations[0]]
    )
    return face_encodings[0].tolist()