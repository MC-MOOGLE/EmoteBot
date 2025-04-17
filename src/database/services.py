import uuid
import shutil
from pathlib import Path
from sqlalchemy import and_, not_
from sqlalchemy.orm import Session
from .models import Image
from ..emote_processor.face_embedding import get_face_embedding
from .database import SessionLocal

def save_image(
    image_path: str,
    emotion: str,
    user_id: str
) -> str:
    # Генерация UUID и путей
    image_uuid = uuid.uuid4()
    target_dir = Path("images")
    target_dir.mkdir(exist_ok=True)
    target_path = target_dir / f"{image_uuid}.jpg"
    
    # Копирование файла
    shutil.copy(image_path, target_path)
    
    # Получение эмбеддинга
    try:
        embedding = get_face_embedding(image_path)
    except Exception as e:
        target_path.unlink()
        raise e
    
    # Сохранение в БД
    with SessionLocal() as session:
        image = Image(
            id=image_uuid,
            user_id=uuid.UUID(user_id),
            emotion=emotion,
            file_path=str(target_path),
            embedding=embedding
        )
        session.add(image)
        session.commit()
    
    return str(image_uuid)

def find_similar_images(
    original_image_id: str,
    find_n: int,
    same_emotion: bool = False
) -> list:
    with SessionLocal() as session:
        # Получение исходного изображения
        original = session.query(Image).get(uuid.UUID(original_image_id))
        if not original:
            return []
        
        # Построение запроса
        query = session.query(Image).filter(
            and_(
                Image.user_id != original.user_id,
                Image.emotion == original.emotion if same_emotion else True
            )
        ).order_by(
            Image.embedding.cosine_distance(original.embedding)
        ).limit(find_n)
        
        return [{
            "id": str(img.id),
            "file_path": img.file_path,
            "user_id": str(img.user_id),
            "emotion": img.emotion
        } for img in query]