from sqlalchemy import Column, String, text
from sqlalchemy.dialects.postgresql import UUID
from .database import Base
from pgvector.sqlalchemy import Vector

class Image(Base):
    __tablename__ = "images"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    user_id = Column(UUID(as_uuid=True), nullable=False)
    emotion = Column(String(50), nullable=False)
    file_path = Column(String(255), nullable=False)
    embedding = Column(Vector(128), nullable=False)  # 128-мерный вектор