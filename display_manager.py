from PIL import Image, ImageDraw, ImageFont, JpegImagePlugin
from io import BytesIO
import requests
import time

class DisplayManager:
    def __init__(self, matrix):
        self.matrix = matrix
        self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
        self.current_image = None
        # Create double buffer
        self.offscreen_canvas = self.matrix.CreateFrameCanvas()
        # Pre-generate common messages
        self._error_image = self._generate_text_image("Error\nRetrying...")
        self._loading_image = self._generate_text_image("Loading...")
        self._art_error_image = self._generate_text_image("Error\nLoading Art")
        
    def _generate_text_image(self, text):
        """Pre-generate text images to avoid repeated creation"""
        image = Image.new('RGB', (64, 64), color='black')
        draw = ImageDraw.Draw(image)
        draw.text((32, 32), text, font=self.font, anchor="mm", fill='white')
        return image

    def show_text(self, text):
        # Check if this is a common message we've pre-generated
        if text == "Error\nRetrying...":
            self.matrix.SetImage(self._error_image)
            return
        elif text == "Loading...":
            self.matrix.SetImage(self._loading_image)
            return
        elif text == "Error\nLoading Art":
            self.matrix.SetImage(self._art_error_image)
            return
            
        # For custom messages, create new image
        if self.current_image:
            try:
                self.current_image.close()
            except Exception as e:
                print(f"Error closing previous image: {e}")
        
        image = self._generate_text_image(text)
        self.matrix.SetImage(image)
        self.current_image = image
    
    def show_album_art(self, url):
        try:
            start_time = time.time()
            print("\n=== Starting show_album_art ===")
            print(f"Timestamp: {time.strftime('%H:%M:%S')}")
            
            # URL hash check
            import hashlib
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            if hasattr(self, '_last_url_hash') and self._last_url_hash == url_hash:
                print("Same image URL detected, skipping update")
                return
            self._last_url_hash = url_hash
            
            # Download
            response = requests.get(url)
            response.raise_for_status()
            
            # Image processing
            with BytesIO(response.content) as image_data:
                with Image.open(image_data) as new_image:
                    # Convert to RGB first
                    if new_image.mode != 'RGB':
                        new_image = new_image.convert('RGB')
                    
                    # Create a new RGB image
                    display_image = Image.new('RGB', (64, 64))
                    
                    # Resize with nearest neighbor sampling
                    resized = new_image.resize((64, 64), Image.Resampling.NEAREST)
                    
                    # Simple copy of the resized image
                    display_image.paste(resized)
                    
                    # Force load into memory
                    display_image.load()
                    
                    # Clean up old image
                    if self.current_image:
                        self.current_image.close()
                    
                    # Update display with double buffering
                    self.offscreen_canvas.SetImage(display_image)
                    self.offscreen_canvas = self.matrix.SwapOnVSync(self.offscreen_canvas)
                    
                    # Store new image
                    self.current_image = display_image
                
            print("=== show_album_art completed ===\n")
            
        except Exception as e:
            print(f"\nError displaying album art: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback:\n{traceback.format_exc()}")
            self.show_text("Error\nLoading Art")
    
    def _slide_transition(self, old_image, new_image):
        try:
            # Pre-generate all frames of the transition
            frames = []
            combined = Image.new('RGB', (64, 128))
            combined.paste(old_image, (0, 0))
            combined.paste(new_image, (0, 64))
            
            for offset in range(65):
                frame = combined.crop((0, offset, 64, offset + 64))
                frames.append(frame.copy())
            
            # Display pre-generated frames with double buffering
            for frame in frames:
                self._update_display(frame)
                time.sleep(0.02)  # Increased from 0.01 to 0.02
                frame.close()
            
            combined.close()
            
        except Exception as e:
            print(f"Error in slide transition: {e}")
            self._update_display(new_image)
    
    def _update_display(self, image):
        """Helper method to update display using double buffering"""
        self.offscreen_canvas.SetImage(image)
        self.offscreen_canvas = self.matrix.SwapOnVSync(self.offscreen_canvas)
    
    def __del__(self):
        # Cleanup when the object is destroyed
        if self.current_image:
            try:
                self.current_image.close()
            except:
                pass
    
    def check_refresh_rate(self):
        """Check the actual refresh rate of the matrix"""
        start_time = time.time()
        frames = 100
        
        test_image = Image.new('RGB', (64, 64), color='black')
        
        for _ in range(frames):
            self.offscreen_canvas.SetImage(test_image)
            self.offscreen_canvas = self.matrix.SwapOnVSync(self.offscreen_canvas)
        
        elapsed = time.time() - start_time
        fps = frames / elapsed
        print(f"Actual refresh rate: {fps:.2f} FPS")
        print(f"Frame time: {(elapsed/frames)*1000:.2f}ms")