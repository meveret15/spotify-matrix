#!/usr/bin/env python3
import time
import logging
from display_manager import DisplayManager
from spotify_client import SpotifyClient
from utils.logger import setup_logger

logger = setup_logger('display', 'logs/display.log', level=logging.INFO)

def main():
    logger.info("Starting Spotify Display Test")
    
    # Initialize display manager and spotify client
    display = DisplayManager()
    spotify = SpotifyClient()
    
    # Track state
    current_track_id = None
    no_track_logged = False
    
    try:
        logger.info("Starting main loop")
        while True:
            track_info = spotify.get_current_track()
            
            if track_info:
                # Generate a unique ID for the track
                track_id = f"{track_info['name']}-{track_info['artist']}"
                
                # Only update display if track has changed
                if track_id != current_track_id:
                    logger.info(f"New track: {track_info['name']} by {track_info['artist']}")
                    display.update_display(track_info['album_art_url'])
                    current_track_id = track_id
                    no_track_logged = False
            else:
                # Only log once when no track is playing
                if not no_track_logged:
                    logger.info("No track currently playing")
                    display.clear_display()
                    current_track_id = None
                    no_track_logged = True
            
            # Poll every 2 seconds
            time.sleep(2)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        display.clear_display()
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
        display.clear_display()

if __name__ == "__main__":
    main()