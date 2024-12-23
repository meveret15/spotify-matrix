import os
import time
import requests
from PIL import Image, ImageDraw, ImageFont, JpegImagePlugin
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
            
            # Enable hardware double-buffering
            matrix_options['disable_hardware_pulsing'] = True
            
            logger.debug(f"Setting matrix options: {matrix_options}")
            for key, value in matrix_options.items():
                logger.debug(f"Setting option {key} = {value}")
                setattr(options, key, value)
            
            logger.debug("Creating RGBMatrix with options")
            self.matrix = RGBMatrix(options=options)
            
            # Create offscreen canvas for double buffering
            self.offscreen_canvas = self.matrix.CreateFrameCanvas()
            
            logger.info("LED Matrix initialized successfully")
            
            logger.debug("Running test pattern")
            self._test_matrix()  # Run test pattern on initialization
            logger.debug("Test pattern completed")
            
        except Exception as e:
            logger.error(f"Failed to initialize LED Matrix: {str(e)}", exc_info=True)
            raise
        
        self.current_image = None
        self.current_art_url = None
        self.matrix_height = 64  # Matrix height for transitions
        self.transition_frames = []  # Store pre-computed transition frames
    
    def _test_matrix(self):
        """Display a test pattern to verify the matrix is working"""
        try:
            logger.info("Displaying test pattern")
            # Create a test image with red, green, and blue squares
            test_image = Image.new('RGB', (64, 64))
            for x in range(32):
                for y in range(32):
                    test_image.putpixel((x, y), (255, 0, 0))  # Red top-left
                    test_image.putpixel((x+32, y), (0, 255, 0))  # Green top-right
                    test_image.putpixel((x, y+32), (0, 0, 255))  # Blue bottom-left
                    test_image.putpixel((x+32, y+32), (255, 255, 255))  # White bottom-right
            
            # Use double buffering for test pattern
            self.offscreen_canvas.SetImage(test_image)
            self.offscreen_canvas = self.matrix.SwapOnVSync(self.offscreen_canvas)
            
            logger.info("Test pattern displayed successfully")
            time.sleep(5)  # Show test pattern for 5 seconds
            
            # Clear using double buffering
            self.offscreen_canvas.Clear()
            self.offscreen_canvas = self.matrix.SwapOnVSync(self.offscreen_canvas)
            test_image.close()
            
        except Exception as e:
            logger.error(f"Error displaying test pattern: {e}")
    
    def download_album_art(self, url):
        """Download album art from URL"""
        logger.debug(f"Downloading album art from: {url}")
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            logger.debug("\nDEBUG INFO:")
            logger.debug(f"URL: {url}")
            logger.debug(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
            logger.debug(f"Content-Length: {len(response.content)} bytes")
            
            # Use context manager for BytesIO to ensure proper cleanup
            with BytesIO(response.content) as image_data:
                # Try to open with PIL
                logger.debug("Attempting to open image with PIL")
                try:
                    new_image = Image.open(image_data)
                    # Create a copy of the image to avoid issues with the closed file
                    logger.debug("Creating copy of image")
                    new_image = new_image.copy()
                    logger.debug(f"Successfully opened image: format={new_image.format}, mode={new_image.mode}, size={new_image.size}")
                    
                    # Convert to RGB if needed
                    if new_image.mode != 'RGB':
                        logger.debug(f"Converting from {new_image.mode} to RGB")
                        new_image = new_image.convert('RGB')
                    
                    logger.debug("Successfully downloaded and processed image")
                    return new_image
                except Exception as e:
                    logger.error(f"Error opening image with PIL: {e}", exc_info=True)
                    return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading album art: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading album art: {e}", exc_info=True)
            return None
    
    def resize_image(self, image):
        """Resize image to fit matrix dimensions"""
        try:
            logger.debug(f"Resizing image from {image.size} to (64, 64)")
            # Resize the image with high-quality resampling
            display_image = image.resize((64, 64), Image.Resampling.LANCZOS)
            logger.debug(f"Successfully resized to {display_image.size}")
            return display_image
            
        except Exception as e:
            logger.error(f"Error resizing image: {e}", exc_info=True)
            return None
    
    def _precompute_transition_frames(self, new_image, steps=32):
        """Precompute all transition frames for smoother animation"""
        logger.debug("Precomputing transition frames")
        frames = []
        
        try:
            if self.current_image is None:
                # Sliding in from top
                for i in range(steps + 1):
                    composite = Image.new('RGB', (64, 64), color='black')
                    offset = int((i * self.matrix_height) / steps)
                    if offset > 0:
                        region = new_image.crop((0, 0, 64, min(offset, 64)))
                        composite.paste(region, (0, 0))
                    frames.append(composite)
            else:
                # Sliding down while pushing old image
                for i in range(steps + 1):
                    composite = Image.new('RGB', (64, 64), color='black')
                    offset = int((i * self.matrix_height) / steps)
                    
                    # Draw current image (moving down)
                    if offset < 64:
                        region = self.current_image.crop((0, 0, 64, 64 - offset))
                        composite.paste(region, (0, offset))
                    
                    # Draw new image (coming from top)
                    if offset > 0:
                        region = new_image.crop((0, max(0, 64 - offset), 64, 64))
                        composite.paste(region, (0, 0))
                    
                    frames.append(composite)
            
            logger.debug(f"Successfully precomputed {len(frames)} transition frames")
            return frames
            
        except Exception as e:
            logger.error(f"Error precomputing transition frames: {e}", exc_info=True)
            return []
    
    def _animate_slide_down(self, new_image, steps=32):
        """Animate new image sliding down over the current image"""
        try:
            logger.debug("Starting slide-down animation")
            
            # Precompute transition frames
            self.transition_frames = self._precompute_transition_frames(new_image, steps)
            
            if not self.transition_frames:
                logger.error("No transition frames generated")
                return
            
            # Calculate frame timing for smooth animation
            frame_time = 0.016  # Target 60fps (1/60 ≈ 0.016s)
            last_frame_time = time.time()
            
            # Clear the canvas before starting animation
            self.offscreen_canvas.Clear()
            self.offscreen_canvas = self.matrix.SwapOnVSync(self.offscreen_canvas)
            
            # Display each frame with proper timing
            for frame in self.transition_frames:
                # Wait for next frame time
                current_time = time.time()
                sleep_time = max(0, frame_time - (current_time - last_frame_time))
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
                # Display frame using double buffering
                self.offscreen_canvas.SetImage(frame)
                self.offscreen_canvas = self.matrix.SwapOnVSync(self.offscreen_canvas)
                
                last_frame_time = time.time()
            
            # Clean up transition frames
            for frame in self.transition_frames:
                frame.close()
            self.transition_frames = []
            
            logger.debug("Slide-down animation completed")
            
        except Exception as e:
            logger.error(f"Error during slide-down animation: {e}", exc_info=True)
            # Ensure the new image is displayed even if animation fails
            self.offscreen_canvas.SetImage(new_image)
            self.offscreen_canvas = self.matrix.SwapOnVSync(self.offscreen_canvas)
    
    def display_image(self, image):
        """Display image on LED matrix"""
        try:
            logger.debug("Preparing to display image")
            
            # Ensure image is in correct format
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Set the image directly
            logger.debug(f"Setting image on matrix (mode={image.mode}, size={image.size})")
            self.matrix.Clear()
            self.matrix.SetImage(image)
            
            # Store the current image
            if self.current_image:
                self.current_image.close()
            self.current_image = image
            
            logger.info("Successfully displayed image on matrix")
            return True
            
        except Exception as e:
            logger.error(f"Error displaying image: {e}", exc_info=True)
            return False
    
    def update_display(self, album_art_url):
        """Update display with new album art"""
        try:
            if album_art_url != self.current_art_url:
                logger.info(f"New album art URL detected: {album_art_url}")
                image = self.download_album_art(album_art_url)
                if image:
                    logger.debug("Successfully downloaded image, resizing...")
                    resized_image = self.resize_image(image)
                    # Clean up the original image as it's no longer needed
                    image.close()
                    
                    if resized_image:
                        logger.debug("Successfully resized image, displaying...")
                        if self.display_image(resized_image):
                            self.current_art_url = album_art_url
                            logger.info("Successfully updated display with new album art")
                            return True
                        else:
                            logger.error("Failed to display resized image")
                            resized_image.close()
                    else:
                        logger.error("Failed to resize image")
                else:
                    logger.error("Failed to download album art")
            else:
                logger.debug("Album art URL unchanged, skipping update")
            return False
        except Exception as e:
            logger.error(f"Error updating display: {e}", exc_info=True)
            return False
    
    def clear_display(self):
        """Clear the LED matrix display"""
        try:
            logger.debug("Clearing LED matrix display")
            self.offscreen_canvas.Clear()
            self.offscreen_canvas = self.matrix.SwapOnVSync(self.offscreen_canvas)
            if self.current_image:
                self.current_image.close()
            self.current_image = None
            self.current_art_url = None
            logger.info("Successfully cleared display")
            return True
        except Exception as e:
            logger.error(f"Error clearing display: {e}")
            return False
            
    def __del__(self):
        """Cleanup when the object is destroyed"""
        if self.current_image:
            try:
                self.current_image.close()
            except:
                pass
        # Clean up any remaining transition frames
        for frame in self.transition_frames:
            try:
                frame.close()
            except:
                pass