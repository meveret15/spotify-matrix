from rgbmatrix import RGBMatrix
from display_manager import DisplayManager
from spotify_client import SpotifyClient
from wifi_manager import WifiManager
from config import get_matrix_options
import time

def main():
    # Matrix configuration
    matrix = RGBMatrix(options=get_matrix_options())
    display = DisplayManager(matrix)
    display.check_refresh_rate()
    
    # Show welcome screen
    display.show_text("SPOTLIGHT")
    
    # Initialize components
    spotify = SpotifyClient()
    wifi_manager = WifiManager(spotify)
    
    # Main application loop
    run_display_loop(display, spotify)

def run_display_loop(display, spotify):
    last_art_url = None
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