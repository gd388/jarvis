"""
Logging configuration and shared utilities for Jarvis Assistant.
"""

import contextlib
import logging
import os
from datetime import datetime
from config.settings import settings


@contextlib.contextmanager
def suppress_c_stderr():
    """
    Redirect C-level file-descriptor 2 (stderr) to /dev/null for the duration
    of the block.  This silences low-level library noise (ALSA dlmisc, Jack)
    that bypasses Python's logging and the ALSA error-handler.

    Python's own stderr (sys.stderr) is unaffected because it is flushed and
    then restored via dup2.
    """
    import sys
    sys.stderr.flush()
    devnull_fd = os.open(os.devnull, os.O_WRONLY)
    old_fd = os.dup(2)
    os.dup2(devnull_fd, 2)
    os.close(devnull_fd)
    try:
        yield
    finally:
        sys.stderr.flush()
        os.dup2(old_fd, 2)
        os.close(old_fd)


def setup_logger(name: str) -> logging.Logger:
    """
    Setup logger with both console and file handlers.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Format for logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    log_file = f"logs/jarvis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger
