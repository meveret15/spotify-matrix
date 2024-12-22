import os
import sys
from rgbmatrix import RGBMatrix
from display_manager import DisplayManager
from spotify_client import SpotifyClient
from wifi_manager import WifiManager
from config import get_matrix_options
import time
import subprocess

def get_ip_address():
    """Get the IP address we should bind to"""
    try:
        result = subprocess.check_output(['hostname', '-I']).decode('utf-8')
        return result.strip().split()[0]
    except:
        return '0.0.0.0'

def main():
    # Check root privileges
    if os.geteuid() != 0:
        sys.exit("Script must run as root. Please run with: sudo python setup.py")
    
    # Initialize components
    matrix = RGBMatrix(options=get_matrix_options())
    display = DisplayManager(matrix)
    spotify = SpotifyClient()
    wifi_manager = WifiManager(spotify, display)
    
    # Start setup or display mode
    if spotify.is_authenticated():
        run_display_mode(matrix, display, spotify)
    else:
        start_setup(spotify, wifi_manager, display)

def start_setup(spotify, wifi_manager, display):
    ip_address = get_ip_address()
    display.show_text(f"Setup at:\n{ip_address}\n:8080")
    wifi_manager.start_setup(host=ip_address, port=8080)

def run_display_mode(matrix, display, spotify):
    """Local version of display loop"""
    # Show welcome screen
    display.show_text("SPOTLIGHT")
    
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