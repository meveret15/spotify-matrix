from PIL import Image
from rgbmatrix import RGBMatrix, RGBMatrixOptions

# Configuration for the matrix
options = RGBMatrixOptions()
options.rows = 64
options.cols = 64
options.chain_length = 1
options.parallel = 1
options.hardware_mapping = 'adafruit-hat'  # Change to 'regular' if not using Adafruit HAT

matrix = RGBMatrix(options = options)

# Create a simple test image
image = Image.new('RGB', (64, 64), color = 'red')
matrix.SetImage(image)

# Keep the script running
input("Press Enter to exit...")