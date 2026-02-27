"""
Logging configuration for the stock analysis platform.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

import config


def setup_logger(name: str = "stock_analysis", log_file: Path = None) -> logging.Logger:
    """
    Setup and configure logger with file and console handlers.
    
    Args:
        name: Logger name
        log_file: Path to log file (defaults to config.LOG_FILE)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, config.LOG_LEVEL))
    
    # Create formatter
    formatter = logging.Formatter(config.LOG_FORMAT)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file is None:
        log_file = config.LOG_FILE
    
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=config.LOG_MAX_BYTES,
            backupCount=config.LOG_BACKUP_COUNT
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not setup file handler: {e}")
    
    return logger


# Create default logger
logger = setup_logger()


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module."""
    return logging.getLogger(f"stock_analysis.{name}")
