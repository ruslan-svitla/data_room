# app/core/logging.py

import logging
import sys
from typing import Any

from loguru import logger
from pydantic import BaseModel

from app.core.config import settings


class LogConfig(BaseModel):
    """Logging configuration for the service."""

    LOG_LEVEL: str = "DEBUG" if settings.DEBUG else "INFO"
    LOG_FORMAT: str = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"


class InterceptHandler(logging.Handler):
    """
    Intercepts standard logging messages and redirects them to Loguru.
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging() -> None:
    """
    Configure a simple, serverless-friendly logger.
    """
    config = LogConfig()

    # 1. Remove any existing handlers
    logger.remove()

    # 2. Add one handler that logs to stderr (for CloudWatch)
    #    This is the CRITICAL FIX: enqueue=False
    logger.add(
        sys.stderr,
        format=config.LOG_FORMAT,
        level=config.LOG_LEVEL,
        enqueue=False,  # Must be False for AWS Lambda
    )

    # 3. Intercept standard logging to redirect it to Loguru
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    logger.info(
        f"Logging initialized for serverless environment at level: {config.LOG_LEVEL}"
    )


def get_logger() -> Any:
    """Return configured logger instance."""
    return logger
