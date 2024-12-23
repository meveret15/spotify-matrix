import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from utils.logger import setup_logger
from config import (
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    SPOTIFY_REDIRECT_URI,
    CACHE_DIR
)

logger = setup_logger('spotify', 'spotify.log')

class SpotifyClient:
    def __init__(self):
        """Initialize the Spotify client"""
        logger.info("Initializing SpotifyClient")
        self.client = None
        logger.debug(f"Using cache path: {os.path.join(CACHE_DIR, '.spotify-token-cache')}")
        self.auth_manager = SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            scope='user-read-playback-state user-modify-playback-state',
            open_browser=False,
            cache_path=os.path.join(CACHE_DIR, '.spotify-token-cache')
        )
        logger.info("SpotifyOAuth manager initialized")
        self._load_client()
    
    def _load_client(self):
        """Load or refresh the Spotify client"""
        try:
            logger.debug("Getting cached token")
            token_info = self.auth_manager.get_cached_token()
            if token_info:
                logger.debug("Found cached token")
                if self.auth_manager.is_token_expired(token_info):
                    logger.info("Token expired, refreshing...")
                    token_info = self.auth_manager.refresh_access_token(token_info['refresh_token'])
                self.client = spotipy.Spotify(auth=token_info['access_token'])
                logger.info("Successfully initialized Spotify client")
                return True
            else:
                logger.warning("No cached token found")
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
            
            logger.debug("Fetching current playback state")
            current = self.client.current_playback()
            
            if current and current.get('item'):
                track_info = {
                    'name': current['item']['name'],
                    'artist': current['item']['artists'][0]['name'],
                    'album': current['item']['album']['name'],
                    'album_art_url': current['item']['album']['images'][0]['url']
                }
                logger.info(f"Current track: {track_info['name']} by {track_info['artist']}")
                return track_info
            else:
                logger.debug("No track currently playing")
                return None
                
        except Exception as e:
            logger.error(f"Error getting current track: {e}")
            # Try to refresh token on error
            if "token expired" in str(e).lower():
                logger.info("Token expired, attempting to reload client")
                self._load_client()
        return None