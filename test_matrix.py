import os
from PIL import Image
from rgbmatrix import RGBMatrix, RGBMatrixOptions

# Configuration for the matrix
options = RGBMatrixOptions()
options.rows = 64
options.cols = 64
options.chain_length = 1
options.parallel = 1
options.hardware_mapping = 'adafruit-hat'

# Optimize for image stability
options.gpio_slowdown = 4
options.brightness = 80
options.pwm_bits = 11
options.pwm_lsb_nanoseconds = 130
options.scan_mode = 1
options.multiplexing = 0
options.limit_refresh_rate_hz = 120

matrix = RGBMatrix(options = options)

try:
    # Test with a bright red color for better visibility
    image = Image.new('RGB', (64, 64), color = 'red')
    matrix.SetImage(image)
    print("Image set to matrix. You should see a red screen.")
    
    # Keep the script running
    input("Press Enter to exit...")

except Exception as e:
    print(f"An error occurred: {e}")
finally:
    matrix.Clear()  # Clean up