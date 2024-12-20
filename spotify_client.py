import os
from config import SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, REDIRECT_URI
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time

class SpotifyClient:
    def __init__(self):
        # Create cache directory in the project folder
        cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
        if not os.path.exists(cache_dir):
            try:
                os.makedirs(cache_dir)
            except:
                # If we can't create the directory, use /tmp
                cache_dir = '/tmp'
        
        cache_path = os.path.join(cache_dir, '.spotify_cache')

        os.environ['SPOTIPY_CLIENT_ID'] = SPOTIPY_CLIENT_ID
        os.environ['SPOTIPY_CLIENT_SECRET'] = SPOTIPY_CLIENT_SECRET
        os.environ['SPOTIPY_REDIRECT_URI'] = REDIRECT_URI

        self.auth_manager = SpotifyOAuth(
            client_id=SPOTIPY_CLIENT_ID,
            client_secret=SPOTIPY_CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope="user-read-currently-playing",
            open_browser=False,
            cache_path=cache_path
        )
        
        self.sp = None

    def is_authenticated(self):
        try:
            if self.sp:
                self.sp.current_user()
                return True
        except:
            pass
        return False

    def get_auth_url(self):
        auth_url = self.auth_manager.get_authorize_url()
        print("\n=== Spotify Authentication Required ===")
        print(f"\nPlease visit this URL in your browser to authenticate:\n\n{auth_url}\n")
        print("After authorizing, you will be redirected. Copy the URL you are redirected to.\n")
        return auth_url

    def wait_for_auth(self):
        while True:
            try:
                print("\nPaste the URL you were redirected to:")
                redirect_url = input().strip()
                
                if 'code=' not in redirect_url:
                    print("Invalid URL. Please make sure to copy the entire URL after redirection.")
                    continue
                
                code = self.auth_manager.parse_response_code(redirect_url)
                token_info = self.auth_manager.get_access_token(code)
                self.sp = spotipy.Spotify(auth_manager=self.auth_manager)
                print("Authentication successful!")
                return True
                
            except Exception as e:
                print(f"Error: {e}")
                print("Please try again.")

    def get_current_track(self):
        try:
            current = self.sp.current_user_playing_track()
            if current and current.get('item'):
                return {
                    'album_art_url': current['item']['album']['images'][0]['url']
                }
            return None
        except:
            return None