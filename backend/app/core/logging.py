import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger
from pydantic import BaseModel

from app.core.config import settings


class LogConfig(BaseModel):
    """Logging configuration to be set for the service"""

    LOGGER_NAME: str = "data_room_api"
    LOG_FORMAT: str = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    LOG_LEVEL: str = "DEBUG" if settings.DEBUG else "INFO"
    LOG_FILE_PATH: Path | None = (
        Path(settings.LOG_DIR)
        / f"{LOGGER_NAME}_{datetime.now().strftime('%Y-%m-%d')}.log"
        if settings.LOG_DIR
        else None
    )


class InterceptHandler(logging.Handler):
    """
    Default handler from examples in loguru documentation.
    See https://loguru.readthedocs.io/en/stable/overview.html#entirely-compatible-with-standard-logging
    """

    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging() -> None:
    """Configure Loguru's logger"""
    config = LogConfig()

    # Remove default handlers
    logger.remove()

    # Add console handler
    logger.add(
        sys.stderr,
        format=config.LOG_FORMAT,
        level=config.LOG_LEVEL,
        enqueue=True,
    )

    # Add file handler if log path is configured
    if config.LOG_FILE_PATH:
        log_dir = config.LOG_FILE_PATH.parent
        log_dir.mkdir(exist_ok=True, parents=True)

        logger.add(
            config.LOG_FILE_PATH,
            format=config.LOG_FORMAT,
            level=config.LOG_LEVEL,
            rotation="00:00",  # New file daily at midnight
            compression="zip",  # Compress rotated logs
            retention="30 days",  # Keep logs for 30 days
            enqueue=True,  # Use queue for thread-safe logging
        )

    # Intercept standard library logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Disable uvicorn access logger
    for logger_name in ("uvicorn.access", "uvicorn", "fastapi"):
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]

    # Set Loguru's logger as the main logger
    logger.configure(handlers=[{"sink": sys.stderr, "level": config.LOG_LEVEL}])

    logger.info(f"Logging initialized at level: {config.LOG_LEVEL}")


def get_logger() -> Any:
    """Return configured logger instance"""
    return logger
