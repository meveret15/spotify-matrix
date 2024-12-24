#!/usr/bin/env python3
import os
import time
import signal
import sys
from utils.logger import setup_logger

# Set up logging first
logger = setup_logger('main', 'main.log')
logger.info("Starting spotify_display_main.py")

from display_manager import DisplayManager
from spotify_client import SpotifyClient
from utils.network import wait_for_network
from config import AUTH_SERVER_PORT, get_local_ip
from spotipy.oauth2 import SpotifyOAuth
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI

logger = setup_logger('main', 'main.log')

def check_auth_token():
    """Check if the auth token exists and is valid"""
    try:
        auth_manager = SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            scope='user-read-playback-state user-modify-playback-state',
            open_browser=False
        )
        token_info = auth_manager.get_cached_token()
        return token_info is not None and not auth_manager.is_token_expired(token_info)
    except:
        return False

class SpotifyDisplay:
    def __init__(self):
        """Initialize the Spotify Display application"""
        logger.info("Initializing SpotifyDisplay")
        self.running = True
        
        try:
            logger.debug("Initializing DisplayManager")
            self.display = DisplayManager()
            logger.info("DisplayManager initialized successfully")
            
            # Show startup sequence
            self.display.display_startup_sequence()
            
            # Check if we need auth
            if not check_auth_token():
                logger.info("No auth token found, starting auth flow")
                self.display.display_text("Visit", duration=2)
                ip = get_local_ip()
                if ip:
                    # Keep showing IP until authenticated
                    while not check_auth_token() and self.running:
                        self.display.display_text(f"{ip}\n:{AUTH_SERVER_PORT}", duration=2)
                        time.sleep(0.5)  # Small pause between refreshes
                    
                    if not self.running:
                        return
                else:
                    logger.error("Could not get local IP address")
                    return
            
        except Exception as e:
            logger.error(f"Failed to initialize DisplayManager: {e}")
            raise
            
        try:
            logger.debug("Initializing SpotifyClient")
            self.spotify = SpotifyClient()
            logger.info("SpotifyClient initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize SpotifyClient: {e}")
            raise
            
        signal.signal(signal.SIGTERM, self.handle_signal)
        signal.signal(signal.SIGINT, self.handle_signal)
        logger.info("Signal handlers registered")
    
    def handle_signal(self, signum, frame):
        """Handle termination signals"""
        logger.info(f"Received signal {signum}")
        self.running = False
    
    def run(self):
        """Main application loop"""
        logger.info("Starting Spotify Display")
        
        # Wait for network connection
        if not wait_for_network():
            logger.error("Failed to connect to network")
            return
        
        last_track = None
        error_count = 0
        no_track_logged = False
        
        while self.running:
            try:
                logger.debug("Fetching current track from Spotify")
                current_track = self.spotify.get_current_track()
                
                if current_track:
                    # Generate a unique ID for the track
                    track_id = f"{current_track['name']}-{current_track['artist']}"
                    
                    if track_id != last_track:
                        logger.info(f"New track: {current_track['name']} by {current_track['artist']}")
                        logger.debug(f"Album art URL: {current_track['album_art_url']}")
                        self.display.update_display(current_track['album_art_url'])
                        last_track = track_id
                        no_track_logged = False
                        error_count = 0
                    else:
                        logger.debug("Same track playing, no update needed")
                else:
                    # Only log once when no track is playing
                    if not no_track_logged:
                        logger.info("No track playing, clearing display")
                        self.display.clear_display()
                        last_track = None
                        no_track_logged = True
                    else:
                        logger.debug("No track playing, display already cleared")
                
                time.sleep(2)  # Reduced polling frequency to match Spotify's rate limits
            
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                error_count += 1
                
                if error_count > 5:
                    logger.error("Too many errors, exiting")
                    break
                
                time.sleep(5)
        
        # Cleanup
        self.display.clear_display()
        logger.info("Spotify Display stopped")

if __name__ == "__main__":
    try:
        app = SpotifyDisplay()
        app.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1) 