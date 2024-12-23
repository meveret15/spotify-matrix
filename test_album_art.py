#!/usr/bin/env python3
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image, ImageDraw, ImageFont, JpegImagePlugin
import time
import requests
from io import BytesIO
import logging
from config import get_matrix_options

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('test_album_art')

# Test with a known album art URL (Spotify's format)
TEST_ALBUM_ART_URL = "https://i.scdn.co/image/ab67616d0000b273e8b066f70c206551210d902b"

def setup_matrix():
    """Initialize the LED matrix with proper options"""
    options = RGBMatrixOptions()
    matrix_options = get_matrix_options()
    
    for key, value in matrix_options.items():
        setattr(options, key, value)
    
    return RGBMatrix(options=options)

def show_album_art(matrix, url):
    """Display album art on the matrix using the working version's approach"""
    try:
        # Download the album art
        response = requests.get(url)
        response.raise_for_status()
        
        logger.debug("\nDEBUG INFO:")
        logger.debug(f"URL: {url}")
        logger.debug(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
        logger.debug(f"Content-Length: {len(response.content)} bytes")
        
        # Use context manager for BytesIO to ensure proper cleanup
        with BytesIO(response.content) as image_data:
            # Try to open with PIL
            new_image = Image.open(image_data)
            # Create a copy of the image to avoid issues with the closed file
            new_image = new_image.copy()
            logger.debug(f"Successfully opened image: format={new_image.format}, mode={new_image.mode}, size={new_image.size}")
            
            # Convert to RGB if needed
            if new_image.mode != 'RGB':
                logger.debug(f"Converting from {new_image.mode} to RGB")
                new_image = new_image.convert('RGB')
            
            # Resize the image
            display_image = new_image.resize((64, 64), Image.Resampling.LANCZOS)
            logger.debug(f"Resized to {display_image.size}")
            
            # Clean up the original image as it's no longer needed
            new_image.close()
            
            # Display the image
            matrix.SetImage(display_image)
            logger.info("Image display complete")
            
            return display_image
            
    except Exception as e:
        logger.exception("\nError displaying album art:")
        return None

if __name__ == "__main__":
    try:
        logger.info("Initializing LED matrix...")
        matrix = setup_matrix()
        
        # Show test pattern first
        logger.info("Showing test pattern...")
        test_image = Image.new('RGB', (64, 64))
        for x in range(32):
            for y in range(32):
                test_image.putpixel((x, y), (255, 0, 0))  # Red top-left
                test_image.putpixel((x+32, y), (0, 255, 0))  # Green top-right
                test_image.putpixel((x, y+32), (0, 0, 255))  # Blue bottom-left
                test_image.putpixel((x+32, y+32), (255, 255, 255))  # White bottom-right
        
        matrix.SetImage(test_image)
        time.sleep(5)
        
        logger.info(f"Attempting to display album art from: {TEST_ALBUM_ART_URL}")
        current_image = show_album_art(matrix, TEST_ALBUM_ART_URL)
        
        if current_image:
            logger.info("Album art should now be visible on the display")
            logger.info("Press Ctrl+C to exit")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("\nClearing display...")
                matrix.Clear()
                if current_image:
                    current_image.close()
        else:
            logger.error("Failed to display album art")
            
    except Exception as e:
        logger.exception("An error occurred:") 