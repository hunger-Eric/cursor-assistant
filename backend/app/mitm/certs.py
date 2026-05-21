"""
CA Certificate Manager for MITM proxy
"""
import os
import logging
import platform
import shutil
from pathlib import Path
from app.config import config

logger = logging.getLogger(__name__)


class CertManager:
    CA_CERT_NAME = "mitmproxy-ca-cert.pem"
    CA_KEY_NAME = "mitmproxy-ca-cert.key"
    
    def __init__(self):
        self._cert_dir = Path(os.path.expanduser(config.proxy.cert_dir))
        self._ensure_cert_dir()
    
    def _ensure_cert_dir(self):
        self._cert_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def ca_cert_path(self) -> Path:
        return self._cert_dir / self.CA_CERT_NAME
    
    @property
    def ca_key_path(self) -> Path:
        return self._cert_dir / self.CA_KEY_NAME
    
    def ensure_ca_cert(self) -> bool:
        default_mitm_dir = Path.home() / ".mitmproxy"
        default_cert = default_mitm_dir / self.CA_CERT_NAME
        if default_cert.exists():
            if not self.ca_cert_path.exists():
                shutil.copy(default_cert, self.ca_cert_path)
                shutil.copy(default_mitm_dir / self.CA_KEY_NAME, self.ca_key_path)
            return True
        return self.ca_cert_path.exists()
    
    def get_ca_cert_path(self) -> Path:
        default_mitm_dir = Path.home() / ".mitmproxy"
        default_cert = default_mitm_dir / self.CA_CERT_NAME
        if default_cert.exists():
            return default_cert
        return self.ca_cert_path
    
    def get_ca_cert_content(self) -> bytes:
        cert_path = self.get_ca_cert_path()
        if cert_path.exists():
            return cert_path.read_bytes()
        return b""
    
    def get_install_instructions(self) -> dict:
        system = platform.system()
        if system == "Windows":
            return {"system": "Windows", "steps": ["1. Double-click downloaded .pem file", "2. Click Install Certificate...", "3. Select Local Machine", "4. Select Trusted Root Certification Authorities store", "5. Complete installation"]}
        elif system == "Darwin":
            return {"system": "macOS", "steps": ["1. Double-click .pem file", "2. Keychain Access opens", "3. Find mitmproxy certificate", "4. Right-click > Get Info > Trust > Always Trust"]}
        else:
            return {"system": "Linux", "steps": ["1. sudo cp <cert> /usr/local/share/ca-certificates/", "2. sudo update-ca-certificates"]}
