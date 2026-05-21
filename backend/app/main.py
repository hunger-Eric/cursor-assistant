"""
Cursor Assistant - Main Application
"""
import logging
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import config
from app.database import init_db
from app.routers import providers, stats
from app.mitm.proxy import get_proxy_server
from app.utils.logger import setup_logger
from fastapi.responses import FileResponse

logger = setup_logger(__name__)

# 全局代理服务器实例
proxy_server = None


def start_proxy_in_thread():
    """在后台线程中启动 MITM 代理"""
    global proxy_server
    try:
        proxy_server = get_proxy_server()
        if proxy_server.start():
            logger.info("MITM Proxy server started successfully")
        else:
            logger.error("Failed to start MITM Proxy server")
    except Exception as e:
        logger.error(f"Error starting MITM Proxy: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # 启动 MITM 代理
    proxy_thread = threading.Thread(target=start_proxy_in_thread, daemon=True)
    proxy_thread.start()
    logger.info(f"{config.name} v{config.version} started")
    yield
    # 停止代理
    if proxy_server and proxy_server.is_running:
        try:
            proxy_server.stop()
            logger.info("MITM Proxy server stopped")
        except Exception as e:
            logger.error(f"Error stopping MITM Proxy: {e}")


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
    return {
        "name": config.name,
        "version": config.version,
        "status": "running",
        "proxy_running": proxy_server.is_running if proxy_server else False,
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/api/health")
async def api_health():
    return {"status": "healthy"}


@app.get("/api/proxy/status")
async def proxy_status():
    """获取代理服务器状态"""
    global proxy_server
    return {
        "running": proxy_server.is_running if proxy_server else False,
        "host": config.proxy.host,
        "port": config.proxy.port
    }


@app.get("/api/proxy/start")
async def proxy_start():
    global proxy_server
    if proxy_server is None:
        proxy_server = get_proxy_server()
    started = proxy_server.start()
    return {"running": bool(started)}


@app.get("/api/proxy/stop")
async def proxy_stop():
    global proxy_server
    if proxy_server:
        proxy_server.stop()
    return {"running": False}


@app.get("/api/proxy/cert")
async def get_cert():
    """下载 CA 证书"""
    try:
        cert_path = get_proxy_server().get_ca_cert_path()
        if cert_path.exists():
            return FileResponse(
                path=cert_path,
                filename="cursor-assistant-ca.pem",
                media_type="application/x-pem-file"
            )
        return {"error": "Certificate not found"}
    except Exception as e:
        logger.error(f"Error getting certificate: {e}")
        return {"error": str(e)}


@app.get("/api/proxy/cert/instructions")
async def get_cert_instructions():
    """获取证书安装说明"""
    from app.mitm.certs import CertManager
    return CertManager().get_install_instructions()
