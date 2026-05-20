"""
Cursor Assistant - Main Application
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from app.config import config
from app.database import init_db
from app.routers import providers, stats
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info(f"{config.name} v{config.version} started")
    yield


app = FastAPI(
    title=config.name,
    version=config.version,
    description="MITM Proxy for enabling Chinese domestic AI models in Cursor IDE",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(providers.router)
app.include_router(stats.router)


@app.get("/")
async def root():
    return {"name": config.name, "version": config.version, "status": "running"}


@app.get("/api")
async def api_root():
    return {"name": config.name, "version": config.version, "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/api/health")
async def api_health():
    return {"status": "healthy"}
