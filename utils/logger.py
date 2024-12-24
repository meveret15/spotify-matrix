import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logger(name, log_file, level=logging.DEBUG):
    """Set up a rotating logger that limits file size and keeps backup count"""
    # Get absolute path to logs directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logs_dir = os.path.join(base_dir, 'logs')
    
    # Create logs directory if it doesn't exist
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create rotating file handler
    # Max size of 1MB, keep 3 backup files
    handler = RotatingFileHandler(
        os.path.join(logs_dir, log_file),
        maxBytes=1024*1024,  # 1MB
        backupCount=3
    )
    handler.setFormatter(formatter)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers = []
    
    # Add the rotating handler
    logger.addHandler(handler)
    
    return logger