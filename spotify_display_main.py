#!/usr/bin/env python3
import os
import time
import signal
import sys
from display_manager import DisplayManager
from spotify_client import SpotifyClient
from utils.logger import setup_logger
from utils.network import wait_for_network

logger = setup_logger('main', 'main.log')

class SpotifyDisplay:
    def __init__(self):
        """Initialize the Spotify Display application"""
        logger.info("Initializing SpotifyDisplay")
        self.running = True
        
        try:
            logger.debug("Initializing DisplayManager")
            self.display = DisplayManager()
            logger.info("DisplayManager initialized successfully")
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
        
        while self.running:
            try:
                logger.debug("Fetching current track from Spotify")
                current_track = self.spotify.get_current_track()
                
                if current_track:
                    if current_track != last_track:
                        logger.info(f"New track: {current_track['name']} by {current_track['artist']}")
                        logger.debug(f"Album art URL: {current_track['album_art_url']}")
                        self.display.update_display(current_track['album_art_url'])
                        last_track = current_track
                        error_count = 0
                    else:
                        logger.debug("Same track playing, no update needed")
                else:
                    if last_track:
                        logger.info("No track playing, clearing display")
                        self.display.clear_display()
                        last_track = None
                    else:
                        logger.debug("No track playing, display already cleared")
                
                time.sleep(1)
            
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