from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config import MYSQL_URL

# 데이터베이스 엔진 생성
engine = create_engine(MYSQL_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 생성
Base = declarative_base()

class Vocabulary(Base):
    """단어장 모델"""
    __tablename__ = "vocabularies"
    
    id = Column(Integer, primary_key=True, index=True)
    vocaId = Column(String(50), unique=True, nullable=False, index=True)
    userId = Column(String(50), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    schoolLevel = Column(String(20), default="중등")
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    items = relationship("VocabularyItem", back_populates="vocabulary")

class VocabularyItem(Base):
    """단어장 항목 모델"""
    __tablename__ = "vocabulary_items"
    
    id = Column(Integer, primary_key=True, index=True)
    word = Column(String(100), nullable=False, index=True)
    meaning = Column(String(200), nullable=False)
    options = Column(Text)  # JSON 형태로 저장
    userId = Column(String(50), nullable=False, index=True)
    vocaId = Column(String(50), ForeignKey("vocabularies.vocaId"), nullable=False, index=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    vocabulary = relationship("Vocabulary", back_populates="items")

# 데이터베이스 테이블 생성
def create_tables():
    Base.metadata.create_all(bind=engine)

# 데이터베이스 세션 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 