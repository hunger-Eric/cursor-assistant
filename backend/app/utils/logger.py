"""
Logging configuration
"""
import logging
import sys
from app.config import config


def setup_logger(name: str = None) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    level = getattr(logging, config.logging.level.upper(), logging.INFO)
    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    formatter = logging.Formatter(config.logging.format)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
