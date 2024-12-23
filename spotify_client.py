import os
import logging
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from utils.logger import setup_logger
from config import (
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    SPOTIFY_REDIRECT_URI
)

logger = setup_logger('spotify', 'spotify.log', level=logging.INFO)

class SpotifyClient:
    def __init__(self):
        """Initialize the Spotify client"""
        logger.info("Initializing SpotifyClient")
        self.client = None
        
        # Set environment variables for Spotipy
        os.environ['SPOTIPY_CLIENT_ID'] = SPOTIFY_CLIENT_ID
        os.environ['SPOTIPY_CLIENT_SECRET'] = SPOTIFY_CLIENT_SECRET
        os.environ['SPOTIPY_REDIRECT_URI'] = SPOTIFY_REDIRECT_URI
        
        # Use default .cache location
        self.auth_manager = SpotifyOAuth(
            scope='user-read-playback-state user-modify-playback-state',
            open_browser=False,
            show_dialog=True  # Force showing the auth dialog
        )
        logger.info("SpotifyOAuth manager initialized")
        self._load_client()
    
    def _load_client(self):
        """Load or refresh the Spotify client"""
        try:
            token_info = self.auth_manager.get_cached_token()
            
            if token_info and not self.auth_manager.is_token_expired(token_info):
                self.client = spotipy.Spotify(auth=token_info['access_token'])
                logger.info("Successfully initialized Spotify client")
                return True
            
            # Try to refresh if we have a token but it's expired
            if token_info and self.auth_manager.is_token_expired(token_info):
                logger.info("Token expired, refreshing...")
                token_info = self.auth_manager.refresh_access_token(token_info['refresh_token'])
                if token_info:
                    self.client = spotipy.Spotify(auth=token_info['access_token'])
                    logger.info("Successfully refreshed token and initialized client")
                    return True
            
            logger.warning("No valid token found - need to authenticate")
            auth_url = self.auth_manager.get_authorize_url()
            logger.info(f"Please visit this URL to authenticate: {auth_url}")
            
        except Exception as e:
            logger.error(f"Error loading client: {e}")
        return False
    
    def get_current_track(self):
        """Get the currently playing track information"""
        try:
            if not self.client:
                logger.warning("No Spotify client available")
                if not self._load_client():
                    return None
            
            current = self.client.current_playback()
            
            if current and current.get('item'):
                track_info = {
                    'name': current['item']['name'],
                    'artist': current['item']['artists'][0]['name'],
                    'album': current['item']['album']['name'],
                    'album_art_url': current['item']['album']['images'][0]['url']
                }
                return track_info
            
            return None
                
        except Exception as e:
            logger.error(f"Error getting current track: {e}")
            # Try to refresh token on error
            if "token expired" in str(e).lower():
                logger.info("Token expired, attempting to reload client")
                self._load_client()
        return None