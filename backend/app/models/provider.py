"""
Provider and Model database models
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Provider(Base):
    __tablename__ = "providers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)
    api_key = Column(Text, nullable=False)
    base_url = Column(String(500), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    models = relationship("Model", back_populates="provider", cascade="all, delete-orphan")


class Model(Base):
    __tablename__ = "models"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    model_id = Column(String(100), nullable=False)
    name = Column(String(100), nullable=False)
    max_tokens = Column(Integer, default=4096)
    supports_streaming = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    parameters = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    provider = relationship("Provider", back_populates="models")
