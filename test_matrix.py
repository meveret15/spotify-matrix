#!/usr/bin/env python3
from rgbmatrix import RGBMatrix, RGBMatrixOptions

def main():
    # Configuration for the matrix
    options = RGBMatrixOptions()
    options.rows = 64
    options.cols = 64
    options.chain_length = 1
    options.parallel = 1
    options.hardware_mapping = 'adafruit-hat'
    options.gpio_slowdown = 4
    options.brightness = 70
    options.disable_hardware_pulsing = True
    options.pwm_lsb_nanoseconds = 50

    print("Creating matrix...")
    matrix = RGBMatrix(options=options)
    print("Matrix created")

    # Fill the screen with red
    print("Filling screen with red...")
    for x in range(64):
        for y in range(64):
            matrix.SetPixel(x, y, 255, 0, 0)
    
    print("Press CTRL+C to exit")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Exiting...")
        matrix.Clear()

if __name__ == "__main__":
    main() 