import time
import requests
from utils.logger import setup_logger
from config import NETWORK_CHECK_URL

logger = setup_logger('network', 'network.log')

def check_network():
    """Check if network is available"""
    try:
        response = requests.get(NETWORK_CHECK_URL, timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Network check failed: {e}")
        return False

def wait_for_network(max_attempts=30, delay=10):
    """Wait for network connection"""
    logger.info("Waiting for network connection...")
    
    for attempt in range(max_attempts):
        if check_network():
            logger.info("Network connection established")
            return True
        
        if attempt < max_attempts - 1:
            logger.info(f"Network check failed, retrying in {delay} seconds...")
            time.sleep(delay)
    
    logger.error("Failed to establish network connection")
    return False 