"""
Centralized logging module for gtckrz application
Provides structured logging with file and console handlers
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path

# Create logs directory if not exists
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

LOG_FILE = LOGS_DIR / f"gtckrz_{datetime.now().strftime('%Y%m%d')}.log"
ERROR_LOG_FILE = LOGS_DIR / "gtckrz_errors.log"


# Configure main logger
def get_logger(name: str, level=logging.INFO) -> logging.Logger:
    """
    Get or create a logger instance with file and console handlers

    Args:
        name: Logger name (typically __name__)
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Create formatters
    detailed_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    simple_formatter = logging.Formatter("%(levelname)s - %(message)s")

    # File handler (detailed) - with rotation
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            LOG_FILE, maxBytes=10485760, backupCount=5  # 10MB
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not create file handler: {e}")

    # Error file handler (errors only)
    try:
        error_handler = logging.handlers.RotatingFileHandler(
            ERROR_LOG_FILE, maxBytes=5242880, backupCount=3  # 5MB
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        logger.addHandler(error_handler)
    except Exception as e:
        print(f"Warning: Could not create error handler: {e}")

    # Console handler (info and above)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)

    return logger


class PerformanceLogger:
    """Helper class for logging performance metrics"""

    def __init__(self, operation_name: str):
        """
        Args:
            operation_name: Name of the operation being timed
        """
        self.operation_name = operation_name
        self.logger = get_logger(__name__)
        self.start_time = None

    def __enter__(self):
        import time

        self.start_time = time.time()
        self.logger.info(f"Starting: {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import time

        elapsed = time.time() - self.start_time

        if exc_type is None:
            self.logger.info(f"Completed: {self.operation_name} in {elapsed:.2f}s")
        else:
            self.logger.error(
                f"Failed: {self.operation_name} after {elapsed:.2f}s - {exc_val}"
            )

        return False


# Module-specific loggers (pre-initialized)
logger = get_logger("gtckrz")
data_logger = get_logger("gtckrz.data")
cache_logger = get_logger("gtckrz.cache")
signal_logger = get_logger("gtckrz.signal")
backtest_logger = get_logger("gtckrz.backtest")
ui_logger = get_logger("gtckrz.ui")
alert_logger = get_logger("gtckrz.alert")
