import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from platformdirs import user_config_dir
import subprocess
from utils.logger import setup_logger
from config import SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, REDIRECT_URI

logger = setup_logger('spotify', 'spotify.log')

class SpotifyClient:
    def __init__(self):
        logger.info("Initializing SpotifyClient")
        self.config_dir = user_config_dir("spotlight", "mever")
        self.cache_path = os.path.join(self.config_dir, '.spotify_cache')
        
        try:
            # Get the actual mever user's UID and GID
            mever_uid = int(subprocess.check_output(['id', '-u', 'mever']).decode().strip())
            mever_gid = int(subprocess.check_output(['id', '-g', 'mever']).decode().strip())
            
            # Create config directory if it doesn't exist
            os.makedirs(self.config_dir, mode=0o755, exist_ok=True)
            os.chown(self.config_dir, mever_uid, mever_gid)
            
            if os.path.exists(self.cache_path):
                os.chown(self.cache_path, mever_uid, mever_gid)
                os.chmod(self.cache_path, 0o600)
                
        except Exception as e:
            logger.error(f"Config directory setup failed: {str(e)}")
            self.config_dir = '/tmp'
            self.cache_path = os.path.join(self.config_dir, '.spotify_cache')
        
        logger.info(f"Using config directory: {self.config_dir}")
        logger.info(f"Using cache path: {self.cache_path}")
        
        self.auth_manager = SpotifyOAuth(
            client_id=SPOTIPY_CLIENT_ID,
            client_secret=SPOTIPY_CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope="user-read-currently-playing user-read-playback-state",
            open_browser=False,
            cache_path=self.cache_path
        )
        
        self.sp = None
        
        # Ensure cache file is writable if it exists
        if os.path.exists(self.cache_path):
            try:
                os.chmod(self.cache_path, 0o666)  # Make writable by all
            except Exception as e:
                print(f"Could not modify cache file permissions: {e}")

    def get_auth_url(self):
        return self.auth_manager.get_authorize_url()
        
    def handle_auth_callback(self, code):
        """Handle the callback from Spotify auth"""
        try:
            token_info = self.auth_manager.get_access_token(code)
            self.sp = spotipy.Spotify(auth_manager=self.auth_manager)
            return True
        except Exception as e:
            print(f"Auth error: {e}")
            return False

    def get_current_track(self):
        """Get the currently playing track"""
        if not self.sp:
            print("Spotify client not initialized")
            return None
        
        try:
            current = self.sp.current_playback()
            if current and current.get('item'):
                return {
                    'name': current['item']['name'],
                    'artist': current['item']['artists'][0]['name'],
                    'album_art_url': current['item']['album']['images'][0]['url']
                }
        except Exception as e:
            print(f"Error getting current track: {e}")
        return None

    def is_authenticated(self):
        """Check if we have valid Spotify credentials"""
        try:
            token_info = self.auth_manager.get_cached_token()
            if token_info and not self.auth_manager.is_token_expired(token_info):
                if not self.sp:
                    self.sp = spotipy.Spotify(auth_manager=self.auth_manager)
                return True
            return False
        except Exception as e:
            print(f"Auth check error: {e}")
            return False