import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from config import LOG_DIR

def setup_logger(name, log_file):
    """Set up and return a logger instance"""
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create log file path
    log_path = os.path.join(LOG_DIR, log_file)
    
    # Create file handler
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=1024 * 1024,  # 1MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Set to DEBUG for more verbose output
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Log initial setup
    logger.info(f"Logger initialized. Logging to: {log_path}")
    logger.debug("Debug logging enabled")
    
    return logger