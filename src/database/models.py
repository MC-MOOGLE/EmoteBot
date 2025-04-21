from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, text, Time
from datetime import time
from sqlalchemy.orm import relationship
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

    user_id = Column(String(128), ForeignKey('users.user_id'), nullable=False) 
    emotion = Column(String(50), nullable=False)
    file_path = Column(String(255), nullable=False)
    embedding = Column(Vector(128), nullable=False)
    created_date = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    
    user = relationship("User", back_populates="images")

class User(Base):
    __tablename__ = 'users'
    user_id = Column(
        String(128),
        primary_key=True,
    )
    images = relationship("Image", back_populates="user")
    settings = relationship("Settings", uselist=False, back_populates="user")

class Settings(Base):
    __tablename__ = 'settings'
    user_id = Column(String(128), ForeignKey('users.user_id'), primary_key=True)
    ai_enabled = Column(Boolean, default=True)
    reminder_time = Column(Time, default=time(20, 0))
    search_allowed = Column(Boolean, default=True)
    user = relationship("User", back_populates="settings")