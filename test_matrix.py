#!/usr/bin/env python3
from display_manager import DisplayManager
import time

if __name__ == "__main__":
    print("Initializing display manager...")
    display = DisplayManager()
    print("Test pattern should be visible for 5 seconds")
    time.sleep(5)  # The test pattern is already shown for 5 seconds in _test_matrix
    print("Done!") 