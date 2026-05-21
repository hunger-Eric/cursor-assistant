"""
MITM Proxy core implementation
"""
import logging
import threading
import asyncio
from typing import Optional
from mitmproxy import options
from mitmproxy.tools.dump import DumpMaster
from app.config import config
from app.mitm.certs import CertManager
from app.mitm.addons.interceptor import CursorInterceptor

logger = logging.getLogger(__name__)


class ProxyServer:
    def __init__(self):
        self._running = False
        self._master: Optional[DumpMaster] = None
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._cert_manager = CertManager()
        
    @property
    def is_running(self) -> bool:
        return self._running
    
    def start(self) -> bool:
        if self._running:
            return True
        try:
            self._cert_manager.ensure_ca_cert()
            self._thread = threading.Thread(target=self._run_proxy, daemon=True)
            self._thread.start()
            self._running = True
            logger.info(f"MITM Proxy started on {config.proxy.host}:{config.proxy.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to start proxy: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def _run_proxy(self):
        """在独立线程中运行 mitmproxy"""
        try:
            # 创建新的事件循环
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            async def _runner():
                opts = options.Options(
                    listen_host=config.proxy.host,
                    listen_port=config.proxy.port,
                    ssl_insecure=True,
                    confdir=str(self._cert_manager._cert_dir.parent),
                )
                self._master = DumpMaster(opts)
                interceptor = CursorInterceptor()
                self._master.addons.add(interceptor)
                await self._master.run()

            self._loop.run_until_complete(_runner())
        except Exception as e:
            logger.error(f"Proxy error: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            self._running = False
    
    def stop(self):
        if not self._running:
            return
        try:
            if self._master:
                self._master.shutdown()
            if self._loop and self._loop.is_running():
                self._loop.call_soon_threadsafe(self._loop.stop)
            self._running = False
            logger.info("MITM Proxy stopped")
        except Exception as e:
            logger.error(f"Error stopping proxy: {e}")
    
    def get_ca_cert_path(self):
        return self._cert_manager.get_ca_cert_path()
    
    def get_ca_cert_content(self) -> bytes:
        return self._cert_manager.get_ca_cert_content()


_proxy_server: Optional[ProxyServer] = None


def get_proxy_server() -> ProxyServer:
    global _proxy_server
    if _proxy_server is None:
        _proxy_server = ProxyServer()
    return _proxy_server
