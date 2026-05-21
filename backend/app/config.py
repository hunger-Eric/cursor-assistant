"""
Configuration management using Pydantic Settings
"""
import os
from pathlib import Path
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProxyConfig(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8080
    cert_dir: str = "~/.cursor-assistant/certs"


class ApiConfig(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: List[str] = ["http://localhost:8080", "http://127.0.0.1:8080"]


class DatabaseConfig(BaseSettings):
    url: str = "sqlite+aiosqlite:///./cursor-assistant.db"


class LoggingConfig(BaseSettings):
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class AppConfig(BaseSettings):
    name: str = "Cursor Assistant"
    version: str = "1.0.0"
    debug: bool = False
    proxy: ProxyConfig = Field(default_factory=ProxyConfig)
    api: ApiConfig = Field(default_factory=ApiConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    model_config = SettingsConfigDict(env_prefix="CMA_", extra="ignore")
    
    @property
    def data_dir(self) -> Path:
        return Path(os.path.expanduser(self.proxy.cert_dir)).parent


config = AppConfig()
