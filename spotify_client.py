import os
import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from utils.logger import setup_logger
from config import (
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    SPOTIFY_REDIRECT_URI,
    CREDENTIALS_FILE
)

logger = setup_logger('spotify', 'spotify.log')

class SpotifyClient:
    def __init__(self):
        """Initialize the Spotify client"""
        self.client = None
        self.auth_manager = SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            scope='user-read-currently-playing',
            open_browser=False
        )
        self._load_credentials()
    
    def _load_credentials(self):
        """Load stored credentials if they exist"""
        try:
            if os.path.exists(CREDENTIALS_FILE):
                with open(CREDENTIALS_FILE, 'r') as f:
                    token_info = json.load(f)
                    if self.auth_manager.is_token_expired(token_info):
                        token_info = self.auth_manager.refresh_access_token(token_info['refresh_token'])
                        self._save_credentials(token_info)
                    self.client = spotipy.Spotify(auth=token_info['access_token'])
                    return True
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
        return False
    
    def _save_credentials(self, token_info):
        """Save credentials to file"""
        try:
            with open(CREDENTIALS_FILE, 'w') as f:
                json.dump(token_info, f)
            return True
        except Exception as e:
            logger.error(f"Error saving credentials: {e}")
            return False
    
    def get_auth_url(self):
        """Get the Spotify authorization URL"""
        try:
            return self.auth_manager.get_authorize_url()
        except Exception as e:
            logger.error(f"Error getting auth URL: {e}")
            return None
    
    def handle_auth_callback(self, code):
        """Handle the authorization callback from Spotify"""
        try:
            token_info = self.auth_manager.get_access_token(code)
            if token_info:
                self._save_credentials(token_info)
                self.client = spotipy.Spotify(auth=token_info['access_token'])
                return True
        except Exception as e:
            logger.error(f"Error handling auth callback: {e}")
        return False
    
    def get_current_track(self):
        """Get the currently playing track information"""
        try:
            if not self.client:
                if not self._load_credentials():
                    return None
            
            current = self.client.current_playback()
            if current and current.get('item'):
                return {
                    'name': current['item']['name'],
                    'artist': current['item']['artists'][0]['name'],
                    'album': current['item']['album']['name'],
                    'album_art_url': current['item']['album']['images'][0]['url']
                }
        except Exception as e:
            logger.error(f"Error getting current track: {e}")
            # Try to refresh token on error
            if "token expired" in str(e).lower():
                self._load_credentials()
        return None