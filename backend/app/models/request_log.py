"""
Request Log model for tracking API usage
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.database import Base


class RequestLog(Base):
    __tablename__ = "request_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(String(100), nullable=False)
    provider_id = Column(String(100), nullable=False)
    provider_type = Column(String(50), nullable=False)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    status = Column(String(20), default="success")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
