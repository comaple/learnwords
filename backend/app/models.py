import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Float, Boolean
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from .db import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

class Upload(Base):
    __tablename__ = 'uploads'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id', ondelete='SET NULL'))
    filename = Column(Text)
    storage_path = Column(Text)
    status = Column(String(20), default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)

class OCRResult(Base):
    __tablename__ = 'ocr_results'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    upload_id = Column(String, ForeignKey('uploads.id', ondelete='CASCADE'))
    raw_json = Column(Text)
    plain_text = Column(Text)
    # store as comma-separated string to avoid Postgres ARRAY requirement in sqlite
    words_extracted = Column(Text)
    count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class Word(Base):
    __tablename__ = 'words'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    lemma = Column(String, unique=True, nullable=False)
    pos = Column(String(32))
    definition = Column(Text)
    pronunciation = Column(Text)
    example = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserWord(Base):
    __tablename__ = 'user_words'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id', ondelete='CASCADE'))
    word_id = Column(String, ForeignKey('words.id', ondelete='CASCADE'))
    added_at = Column(DateTime, default=datetime.utcnow)
    review_count = Column(Integer, default=0)
    last_review_at = Column(DateTime)
    next_review_at = Column(DateTime)
    ease_factor = Column(Float, default=2.5)
    interval_hours = Column(Float, default=0.0)
    performance_history = Column(Text)  # JSON string
