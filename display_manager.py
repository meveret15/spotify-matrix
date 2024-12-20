from PIL import Image, ImageDraw, ImageFont, JpegImagePlugin
from io import BytesIO
import requests
import time

class DisplayManager:
    def __init__(self, matrix):
        self.matrix = matrix
        self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
        self.current_image = None
        
    def show_text(self, text):
        # Close previous image if it exists
        if self.current_image:
            try:
                self.current_image.close()
            except Exception as e:
                print(f"Error closing previous image: {e}")
        
        image = Image.new('RGB', (64, 64), color='black')
        draw = ImageDraw.Draw(image)
        draw.text((32, 32), text, font=self.font, anchor="mm", fill='white')
        self.matrix.SetImage(image)
        self.current_image = image
    
    def show_album_art(self, url):
        try:
            # Download the album art
            response = requests.get(url)
            response.raise_for_status()
            
            print("\nDEBUG INFO:")
            print(f"URL: {url}")
            print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
            print(f"Content-Length: {len(response.content)} bytes")
            
            # Use context manager for BytesIO to ensure proper cleanup
            with BytesIO(response.content) as image_data:
                # Try to open with PIL
                new_image = Image.open(image_data)
                # Create a copy of the image to avoid issues with the closed file
                new_image = new_image.copy()
                print(f"Successfully opened image: format={new_image.format}, mode={new_image.mode}, size={new_image.size}")
                
                # Convert to RGB if needed
                if new_image.mode != 'RGB':
                    print(f"Converting from {new_image.mode} to RGB")
                    new_image = new_image.convert('RGB')
                
                # Resize the image
                display_image = new_image.resize((64, 64), Image.Resampling.LANCZOS)
                print(f"Resized to {display_image.size}")
                
                # Clean up the original image as it's no longer needed
                new_image.close()
                
                # Display the image
                old_image = self.current_image  # Store reference to old image
                if old_image:
                    print("Performing slide transition")
                    self._slide_transition(old_image, display_image)
                    # Close old image after transition
                    old_image.close()
                else:
                    print("Setting image directly")
                    self.matrix.SetImage(display_image)
                
                # Update current image
                self.current_image = display_image
                print("Image display complete")
            
        except Exception as e:
            print(f"\nError displaying album art: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback:\n{traceback.format_exc()}")
            self.show_text("Error\nLoading Art")
    
    def _slide_transition(self, old_image, new_image):
        try:
            # Create a combined image twice the height
            combined = Image.new('RGB', (64, 128))
            combined.paste(old_image, (0, 0))
            combined.paste(new_image, (0, 64))
            
            # Slide up animation
            for offset in range(65):
                # Create a view window that slides up
                view = combined.crop((0, offset, 64, offset + 64))
                self.matrix.SetImage(view)
                time.sleep(0.01)  # Adjust speed as needed
            
            # Clean up the combined image
            combined.close()
            
        except Exception as e:
            print(f"Error in slide transition: {e}")
            # Fallback to direct display if transition fails
            self.matrix.SetImage(new_image)
    
    def __del__(self):
        # Cleanup when the object is destroyed
        if self.current_image:
            try:
                self.current_image.close()
            except:
                pass