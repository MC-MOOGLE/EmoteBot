import uuid
import shutil
from pathlib import Path
from sqlalchemy import and_, true
from datetime import datetime
from .models import Image, User, Settings
from ..emote_processor.face_embedding import get_face_embedding
from .database import SessionLocal

def save_image(
    image_path: str,
    emotion: str,
    user_id: str,
    created_date: datetime | None = None,
) -> str:
    # Генерация UUID и путей
    image_uuid = uuid.uuid4()
    target_dir = Path("images")
    target_dir.mkdir(exist_ok=True)
    target_path = target_dir / f"{image_uuid}.jpg"
    shutil.copy(image_path, target_path)
    
    # Получение эмбеддинга
    try:
        embedding = get_face_embedding(image_path)
    except Exception as e:
        target_path.unlink()
        raise e
    
    # Сохранение в БД
    with SessionLocal() as session:
        if created_date is None:
            created_date = datetime.now()

        image = Image(
            id=image_uuid,
            user_id=str(user_id),
            emotion=emotion,
            file_path=str(target_path),
            embedding=embedding,
            created_date = created_date
        )

        session.add(image)
        session.commit()
    
    return str(image_uuid)

def get_user_data(user_id):
    with SessionLocal() as session:        
        query = session.query(Image).filter(Image.user_id == user_id)
        
        return [{
            "image_path": img.file_path,
            "emotion": img.emotion,
            "created_at": img.created_date
        } for img in query]
    
def get_users(emotion = None):
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    with SessionLocal() as session:
        query = session.query(Image).filter(
            Image.created_date >= today_start
        )
        
        if emotion:
            query = query.filter(Image.emotion == emotion)
        
        unique_user_count = len(set(img.user_id for img in query)) # query.scalar() doesnt work for some reason, will fix later
        return unique_user_count

def find_similar_images(
    image_id: str,
    find_n: int = 5,
    same_emotion: bool = False,
    ignore_original_user: bool = True,
    all_time = False
) -> list:
    with SessionLocal() as session:
        original_image = session.query(Image).get(image_id)

        if not all_time:
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        filters = [Settings.search_allowed == true()]

        if ignore_original_user:
            filters.append(Image.user_id != original_image.user_id)
        if same_emotion:
            filters.append(Image.emotion == original_image.emotion)
        if all_time:
            filters.append(Image.created_date >= today_start)

        query = (session.query(Image).join(User).join(Settings)
            .filter(and_(*filters))
            .order_by(Image.embedding.cosine_distance(original_image.embedding)).limit(find_n)
        ) # Join all tables and apply filters
        
        return [{
            "id": str(img.id),
            "file_path": img.file_path,
            "user_id": str(img.user_id),
            "emotion": img.emotion
        } for img in query]