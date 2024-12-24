import os
import time
import socket
import requests
from PIL import Image, ImageDraw, ImageFont, JpegImagePlugin
from io import BytesIO
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from utils.logger import setup_logger
from config import get_matrix_options, AUTH_SERVER_PORT

logger = setup_logger('display', 'display.log')

class DisplayManager:
    def __init__(self):
        """Initialize the display manager"""
        logger.info("Initializing DisplayManager")
        try:
            logger.debug("Creating RGBMatrixOptions")
            options = RGBMatrixOptions()
            matrix_options = get_matrix_options()
            
            # Set critical display options for reduced flickering
            matrix_options['disable_hardware_pulsing'] = False  # Enable hardware pulsing
            matrix_options['pwm_bits'] = 11  # Increase PWM bits for better color depth
            matrix_options['pwm_lsb_nanoseconds'] = 130  # Adjust PWM timing
            matrix_options['limit_refresh_rate_hz'] = 100  # Set refresh rate limit
            
            logger.debug(f"Setting matrix options: {matrix_options}")
            for key, value in matrix_options.items():
                logger.debug(f"Setting option {key} = {value}")
                setattr(options, key, value)
            
            logger.debug("Creating RGBMatrix with options")
            self.matrix = RGBMatrix(options=options)
            
            # Create offscreen canvas for double buffering
            self.offscreen_canvas = self.matrix.CreateFrameCanvas()
            
            logger.info("LED Matrix initialized successfully")
            
            # Load font for text display
            try:
                # Try to load a nice looking font, fallback to default if not available
                self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 8)  # Smaller regular font
                self.large_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)  # Smaller large font
            except Exception as e:
                logger.warning(f"Could not load custom font, using default: {e}")
                self.font = ImageFont.load_default()
                self.large_font = ImageFont.load_default()
            
        except Exception as e:
            logger.error(f"Failed to initialize LED Matrix: {str(e)}", exc_info=True)
            raise
        
        self.current_image = None
        self.current_art_url = None
        self.matrix_height = 64
    
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

    def _animate_fade(self, new_image, steps=30):
        """Animate fade transition between current and new image"""
        try:
            logger.debug("Starting fade transition")
            
            # Calculate frame timing for smooth animation
            frame_time = 0.016  # Target 60fps (1/60 ≈ 0.016s)
            last_frame_time = time.time()
            
            # Generate and display each frame
            for i in range(steps + 1):
                alpha = i / steps
                
                if self.current_image:
                    # Blend between current and new image
                    frame = Image.blend(self.current_image, new_image, alpha)
                else:
                    # If no current image, fade in from black
                    frame = Image.new('RGB', (64, 64), color='black')
                    frame = Image.blend(frame, new_image, alpha)
                
                # Timing control for smooth animation
                current_time = time.time()
                sleep_time = max(0, frame_time - (current_time - last_frame_time))
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
                # Display frame using double buffering
                self.offscreen_canvas.SetImage(frame)
                self.offscreen_canvas = self.matrix.SwapOnVSync(self.offscreen_canvas)
                
                last_frame_time = time.time()
                
                # Clean up the intermediate frame
                if i < steps:  # Don't close the final frame
                    frame.close()
            
            logger.debug("Fade transition completed")
            
        except Exception as e:
            logger.error(f"Error during fade transition: {e}", exc_info=True)
            # Ensure the new image is displayed even if animation fails
            self.offscreen_canvas.SetImage(new_image)
            self.offscreen_canvas = self.matrix.SwapOnVSync(self.offscreen_canvas)

    def display_image(self, image):
        """Display image on LED matrix with fade transition"""
        try:
            logger.debug("Preparing to display image")
            
            # Ensure image is in correct format
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Animate fade transition to new image
            self._animate_fade(image)
            
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

    def get_local_ip(self):
        """Get the local IP address"""
        try:
            # Create a socket to determine the IP address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            logger.error(f"Error getting local IP: {e}")
            return None

    def create_text_image(self, text, large=False, color=(255, 255, 255)):
        """Create an image with centered text, handling multiple lines with 3D effect"""
        try:
            # Create a new image with black background
            image = Image.new('RGB', (64, 64), color='black')
            draw = ImageDraw.Draw(image)
            
            # Use large font for main messages, regular for IP/status
            font = self.large_font if large else self.font
            
            # Split text into words
            words = text.split()
            lines = []
            current_line = []
            
            # Group words into lines that fit the display
            for word in words:
                test_line = ' '.join(current_line + [word])
                bbox = draw.textbbox((0, 0), test_line, font=font)
                if bbox[2] - bbox[0] <= 60:  # Leave some margin
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
            
            if current_line:
                lines.append(' '.join(current_line))
            
            # If no lines were created (e.g., single word too long), split the text
            if not lines:
                lines = [text[i:i+8] for i in range(0, len(text), 8)]  # 8 chars per line
            
            # Calculate total height of all lines
            line_height = max(font.size * 1.2, 10)  # Add 20% line spacing
            total_height = len(lines) * line_height
            
            # Calculate starting Y position to center all lines vertically
            y = (64 - total_height) // 2
            
            # Draw each line centered horizontally with 3D effect
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                x = (64 - text_width) // 2

                # Create 3D effect with multiple layers
                if large:  # Only add 3D effect for large text
                    # Draw shadow layers (dark to light)
                    shadow_colors = [
                        (int(color[0]*0.2), int(color[1]*0.2), int(color[2]*0.2)),  # Darkest
                        (int(color[0]*0.4), int(color[1]*0.4), int(color[2]*0.4)),
                        (int(color[0]*0.6), int(color[1]*0.6), int(color[2]*0.6)),
                        (int(color[0]*0.8), int(color[1]*0.8), int(color[2]*0.8))
                    ]
                    
                    # Draw shadow layers
                    for i, shadow_color in enumerate(shadow_colors):
                        offset = 3 - i  # Decreasing offset for each layer
                        draw.text((x + offset, y + offset), line, font=font, fill=shadow_color)
                
                # Draw main text
                draw.text((x, y), line, font=font, fill=color)
                y += line_height
            
            return image
        except Exception as e:
            logger.error(f"Error creating text image: {e}")
            return None

    def display_text(self, text, duration=None, large=False, color=(255, 255, 255)):
        """Display text on the LED matrix"""
        try:
            logger.debug(f"Displaying text: {text}")
            text_image = self.create_text_image(text, large, color)
            if text_image:
                self.display_image(text_image)
                if duration:
                    time.sleep(duration)
            return True
        except Exception as e:
            logger.error(f"Error displaying text: {e}")
            return False

    def display_auth_info(self):
        """Display authentication information including IP address"""
        ip = self.get_local_ip()
        if ip:
            self.display_text("Visit", duration=2)
            # Split IP and port into separate lines
            self.display_text(f"{ip}\n:{AUTH_SERVER_PORT}", duration=3)
            self.display_text("to setup", duration=2)
            return True
        return False

    def _create_rainbow_colors(self, steps):
        """Create a list of rainbow colors for animation"""
        colors = []
        for i in range(steps):
            # Create a rainbow cycle
            hue = (i / steps) * 360
            # Convert HSV to RGB (simplified conversion)
            h = hue / 60
            c = 255
            x = int(255 * (1 - abs(h % 2 - 1)))

            if h < 1:
                rgb = (255, x, 0)
            elif h < 2:
                rgb = (x, 255, 0)
            elif h < 3:
                rgb = (0, 255, x)
            elif h < 4:
                rgb = (0, x, 255)
            elif h < 5:
                rgb = (x, 0, 255)
            else:
                rgb = (255, 0, x)
            
            colors.append(rgb)
        return colors

    def _animate_rainbow_text(self, text, duration=3, steps=60):
        """Display text with rainbow animation"""
        try:
            colors = self._create_rainbow_colors(steps)
            start_time = time.time()
            frame_time = duration / steps
            
            while time.time() - start_time < duration:
                for color in colors:
                    text_image = self.create_text_image(text, large=True, color=color)
                    if text_image:
                        self.offscreen_canvas.SetImage(text_image)
                        self.offscreen_canvas = self.matrix.SwapOnVSync(self.offscreen_canvas)
                        text_image.close()
                        time.sleep(frame_time)
            
            return True
        except Exception as e:
            logger.error(f"Error in rainbow animation: {e}")
            return False

    def display_startup_sequence(self):
        """Display the startup sequence"""
        try:
            # Show SPOTLIGHT text with rainbow animation
            self._animate_rainbow_text("SPOT\nLIGHT", duration=3)
            return True
        except Exception as e:
            logger.error(f"Error in startup sequence: {e}")
            return False