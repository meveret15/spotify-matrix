from rgbmatrix import RGBMatrix, RGBMatrixOptions
from display_manager import DisplayManager
from spotify_client import SpotifyClient
from wifi_manager import WifiManager
from PIL import Image
import time
import os

def main():
    # Matrix configuration
    options = RGBMatrixOptions()
    options.rows = 64
    options.cols = 64
    options.hardware_mapping = 'adafruit-hat'
    
    matrix = RGBMatrix(options=options)
    display = DisplayManager(matrix)
    
    # Show welcome screen
    display.show_text("SPOTLIGHT")
    
    # Initialize Spotify client
    spotify = SpotifyClient()
    if not spotify.is_authenticated():
        auth_url = spotify.get_auth_url()
        display.show_text("Check Terminal\nfor Auth URL")
        spotify.wait_for_auth()
    
    # Track the last album art URL to prevent unnecessary updates
    last_art_url = None
    
    # Main loop
    while True:
        try:
            current_track = spotify.get_current_track()
            if current_track and current_track.get('album_art_url'):
                if current_track['album_art_url'] != last_art_url:
                    display.show_album_art(current_track['album_art_url'])
                    last_art_url = current_track['album_art_url']
            time.sleep(1)
        except Exception as e:
            print(f"Error: {str(e)}")
            display.show_text("Error\nRetrying...")
            time.sleep(5)

if __name__ == "__main__":
    main()