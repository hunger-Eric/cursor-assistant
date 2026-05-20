"""
MITM Proxy core implementation
"""
import logging
import threading
from typing import Optional
from mitmproxy import options, master
from mitmproxy.proxy import ProxyServer as MitmProxyServer
from app.config import config
from app.mitm.certs import CertManager
from app.mitm.addons.interceptor import CursorInterceptor

logger = logging.getLogger(__name__)


class ProxyServer:
    def __init__(self):
        self._running = False
        self._master: Optional[master.Master] = None
        self._thread: Optional[threading.Thread] = None
        self._cert_manager = CertManager()
        
    @property
    def is_running(self) -> bool:
        return self._running
    
    def start(self) -> bool:
        if self._running:
            return True
        try:
            self._cert_manager.ensure_ca_cert()
            opts = options.Options(
                listen_host=config.proxy.host,
                listen_port=config.proxy.port,
                ssl_insecure=True,
            )
            self._master = master.Master(opts)
            interceptor = CursorInterceptor()
            self._master.addons.add(interceptor)
            self._thread = threading.Thread(target=self._run_proxy, args=(opts,), daemon=True)
            self._thread.start()
            self._running = True
            logger.info(f"Proxy started on {config.proxy.host}:{config.proxy.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to start proxy: {e}")
            return False
    
    def _run_proxy(self, opts):
        try:
            self._master.run()
        except Exception as e:
            logger.error(f"Proxy error: {e}")
            self._running = False
    
    def stop(self):
        if not self._running:
            return
        try:
            if self._master:
                self._master.shutdown()
            self._running = False
            logger.info("Proxy stopped")
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
