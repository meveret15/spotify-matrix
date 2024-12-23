import os
import time
import requests
import numpy as np
from PIL import Image
from io import BytesIO
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from utils.logger import setup_logger
from config import get_matrix_options

logger = setup_logger('display', 'display.log')

class DisplayManager:
    def __init__(self):
        """Initialize the display manager"""
        logger.info("Initializing DisplayManager")
        try:
            logger.debug("Creating RGBMatrixOptions")
            options = RGBMatrixOptions()
            matrix_options = get_matrix_options()
            
            logger.debug(f"Setting matrix options: {matrix_options}")
            for key, value in matrix_options.items():
                logger.debug(f"Setting option {key} = {value}")
                setattr(options, key, value)
            
            logger.debug("Creating RGBMatrix with options")
            self.matrix = RGBMatrix(options=options)
            logger.info("LED Matrix initialized successfully")
            
            logger.debug("Running test pattern")
            self._test_matrix()  # Run test pattern on initialization
            logger.debug("Test pattern completed")
            
        except Exception as e:
            logger.error(f"Failed to initialize LED Matrix: {str(e)}", exc_info=True)
            raise
        
        self.current_image = None
        self.current_art_url = None
    
    def _test_matrix(self):
        """Display a test pattern to verify the matrix is working"""
        try:
            logger.info("Displaying test pattern")
            # Create a test image with red, green, and blue squares
            width = self.matrix.width
            height = self.matrix.height
            image = Image.new('RGB', (width, height))
            
            # Red square in top-left
            for x in range(width//2):
                for y in range(height//2):
                    image.putpixel((x, y), (255, 0, 0))
            
            # Green square in top-right
            for x in range(width//2, width):
                for y in range(height//2):
                    image.putpixel((x, y), (0, 255, 0))
            
            # Blue square in bottom-left
            for x in range(width//2):
                for y in range(height//2, height):
                    image.putpixel((x, y), (0, 0, 255))
            
            # White square in bottom-right
            for x in range(width//2, width):
                for y in range(height//2, height):
                    image.putpixel((x, y), (255, 255, 255))
            
            self.matrix.SetImage(image.convert('RGB'))
            logger.info("Test pattern displayed successfully")
            time.sleep(5)  # Show test pattern for 5 seconds
            self.matrix.Clear()
            
        except Exception as e:
            logger.error(f"Error displaying test pattern: {e}")
    
    def download_album_art(self, url):
        """Download album art from URL"""
        logger.debug(f"Downloading album art from: {url}")
        try:
            response = requests.get(url)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))
            logger.info(f"Successfully downloaded album art: {image.size}")
            return image
        except Exception as e:
            logger.error(f"Error downloading album art: {e}")
            return None
    
    def resize_image(self, image):
        """Resize image to fit matrix dimensions"""
        try:
            matrix_width = self.matrix.width
            matrix_height = self.matrix.height
            
            # Calculate aspect ratio
            width_ratio = matrix_width / image.width
            height_ratio = matrix_height / image.height
            ratio = min(width_ratio, height_ratio)
            
            new_width = int(image.width * ratio)
            new_height = int(image.height * ratio)
            
            logger.debug(f"Resizing image from {image.size} to ({new_width}, {new_height})")
            
            # Resize image
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Create new image with black background
            new_image = Image.new('RGB', (matrix_width, matrix_height))
            
            # Calculate position to paste resized image
            x = (matrix_width - new_width) // 2
            y = (matrix_height - new_height) // 2
            
            # Paste resized image onto black background
            new_image.paste(image, (x, y))
            logger.info(f"Successfully resized image to {new_image.size}")
            
            return new_image
        except Exception as e:
            logger.error(f"Error resizing image: {e}")
            return None
    
    def display_image(self, image):
        """Display image on LED matrix"""
        try:
            logger.debug("Clearing matrix display")
            self.matrix.Clear()
            
            logger.debug("Converting image to RGB and setting on matrix")
            self.matrix.SetImage(image.convert('RGB'))
            self.current_image = image
            logger.info("Successfully displayed image on matrix")
            return True
        except Exception as e:
            logger.error(f"Error displaying image: {e}")
            return False
    
    def update_display(self, album_art_url):
        """Update display with new album art"""
        try:
            if album_art_url != self.current_art_url:
                logger.info(f"New album art URL detected: {album_art_url}")
                image = self.download_album_art(album_art_url)
                if image:
                    resized_image = self.resize_image(image)
                    if resized_image and self.display_image(resized_image):
                        self.current_art_url = album_art_url
                        logger.info("Successfully updated display with new album art")
                        return True
                    else:
                        logger.warning("Failed to resize or display image")
                else:
                    logger.warning("Failed to download album art")
            else:
                logger.debug("Album art URL unchanged, skipping update")
            return False
        except Exception as e:
            logger.error(f"Error updating display: {e}")
            return False
    
    def clear_display(self):
        """Clear the LED matrix display"""
        try:
            logger.debug("Clearing LED matrix display")
            self.matrix.Clear()
            self.current_image = None
            self.current_art_url = None
            logger.info("Successfully cleared display")
            return True
        except Exception as e:
            logger.error(f"Error clearing display: {e}")
            return False