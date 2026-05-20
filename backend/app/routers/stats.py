"""
Statistics API routes
"""
from fastapi import APIRouter
from sqlalchemy import select, func
from app.models.request_log import RequestLog
from app.database import AsyncSessionLocal

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("")
async def get_stats():
    async with AsyncSessionLocal() as session:
        total_requests = await session.scalar(select(func.count()).select_from(RequestLog))
        total_tokens = await session.scalar(select(func.sum(RequestLog.total_tokens)).select_from(RequestLog))
        success_count = await session.scalar(select(func.count()).select_from(RequestLog).where(RequestLog.status == "success"))
        error_count = await session.scalar(select(func.count()).select_from(RequestLog).where(RequestLog.status == "error"))
        return {"total_requests": total_requests or 0, "total_tokens": total_tokens or 0, "success_count": success_count or 0, "error_count": error_count or 0}
