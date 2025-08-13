import os
import sys
from datetime import datetime
from typing import Optional

from loguru import logger

# Get current date for log file naming
current_date = datetime.now().strftime("%Y-%m-%d")


def setup_logger(
    project_name: str,
    log_dir: Optional[str] = None,
    log_file: Optional[str] = None,
    log_level: str = "DEBUG",
    rotation: str = "500 MB",
    retention: str = "10 days",
    compression: str = "zip",
    format_str: Optional[str] = None,
) -> None:
    """
    Initialize logging configuration for different projects.

    Args:
        project_name: Project name for log directory and filename
        log_dir: Log directory path (auto-generated if None)
        log_file: Log filename (auto-generated if None)
        log_level: Log level (DEBUG, INFO, etc.)
        rotation: Log file rotation size
        retention: Log retention time
        compression: Log compression format
        format_str: Custom log format string
    """
    log_dir = log_dir or f"{project_name}_logs/{current_date}"
    log_file = log_file or f"{project_name}_{current_date}.log"
    format_str = (
        format_str
        or "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
    )

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Clear default log handlers
    logger.remove()

    # Console log handler
    logger.add(
        sys.stdout,
        format=format_str,
        level=log_level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # File log handler
    logger.add(
        f"{log_dir}/{log_file}",
        rotation=rotation,
        retention=retention,
        compression=compression,
        format=format_str,
        level="DEBUG",
        backtrace=True,
        diagnose=True,
    )

    # Error logs stored separately
    logger.add(
        f"{log_dir}/error_{log_file}",
        rotation=rotation,
        retention=retention,
        compression=compression,
        format=format_str,
        level="ERROR",
        backtrace=True,
        diagnose=True,
    )

    logger.debug(f"Logger initialized for project: {project_name}")
    logger.debug(f"Log directory: {log_dir}")
    logger.debug(f"Log level: {log_level}")


def get_logger(name: str):
    """
    Get a logger instance with module name.

    Args:
        name: Module name (usually __name__)

    Returns:
        logger: Configured logger instance
    """
    return logger.bind(name=name)


__all__ = ["setup_logger", "get_logger", "logger"]
