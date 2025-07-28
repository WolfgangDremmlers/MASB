"""Logging configuration for MASB."""

import sys
from pathlib import Path
from loguru import logger
from src.config import settings


def setup_logging():
    """Configure logging for the application."""
    # Remove default handler
    logger.remove()
    
    # Console handler with color
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True
    )
    
    # File handler for all logs
    logger.add(
        settings.logs_dir / "masb_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="1 day",
        retention="30 days",
        compression="zip"
    )
    
    # File handler for errors only
    logger.add(
        settings.logs_dir / "errors_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="1 week",
        retention="60 days",
        compression="zip"
    )
    
    return logger


# Initialize logger
logger = setup_logging()