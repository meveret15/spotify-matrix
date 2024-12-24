from flask import Flask, redirect, request
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import netifaces
from config import (
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    SPOTIFY_REDIRECT_URI,
    AUTH_SERVER_PORT
)
from utils.logger import setup_logger

app = Flask(__name__)
logger = setup_logger('auth', 'auth.log')

# Set environment variables for Spotipy
os.environ['SPOTIPY_CLIENT_ID'] = SPOTIFY_CLIENT_ID
os.environ['SPOTIPY_CLIENT_SECRET'] = SPOTIFY_CLIENT_SECRET
os.environ['SPOTIPY_REDIRECT_URI'] = SPOTIFY_REDIRECT_URI

def get_local_ip():
    # Get IP address of the Pi on the local network
    interfaces = netifaces.interfaces()
    for interface in interfaces:
        if interface.startswith('w'):  # wifi interface
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                ip = addrs[netifaces.AF_INET][0]['addr']
                logger.info(f"Found local IP: {ip}")
                return ip
    logger.warning("Could not find local IP address")
    return None

def clear_auth():
    """Clear the Spotify authentication"""
    try:
        # Remove the cache file
        cache_file = '.cache'
        if os.path.exists(cache_file):
            os.remove(cache_file)
            logger.info("Auth cache cleared")
        return True
    except Exception as e:
        logger.error(f"Error clearing auth: {e}")
        return False

@app.route('/')
def index():
    logger.info("Index page accessed")
    auth_manager = SpotifyOAuth(
        scope='user-read-playback-state user-modify-playback-state',
        open_browser=False,
        show_dialog=True  # Always show dialog for account selection
    )
    
    try:
        if auth_manager.validate_token(auth_manager.get_cached_token()):
            logger.info("Valid token found, showing status page")
            return f'''
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 40px auto; padding: 0 20px; text-align: center; }}
                        h1 {{ color: #1DB954; }}
                        .button {{ display: inline-block; background-color: #1DB954; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; border: none; font-size: 16px; cursor: pointer; margin: 10px; }}
                        .warning {{ color: #e55; margin: 20px 0; }}
                    </style>
                </head>
                <body>
                    <h1>SpotifyMatrix Status</h1>
                    <p>A Spotify account is currently connected and displaying music.</p>
                    <p>Want to switch to a different account?</p>
                    <form action="/reauth" method="post">
                        <button type="submit" class="button">Switch Spotify Account</button>
                    </form>
                    <p class="warning">Note: This will disconnect the current account.</p>
                </body>
                </html>
            '''
    except:
        pass
    
    auth_url = auth_manager.get_authorize_url()
    return f'''
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 40px auto; padding: 0 20px; text-align: center; }}
                h1 {{ color: #1DB954; }}
                .button {{ display: inline-block; background-color: #1DB954; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; margin: 20px; }}
            </style>
        </head>
        <body>
            <h1>Welcome to SpotifyMatrix!</h1>
            <p>Click the button below to connect your Spotify account:</p>
            <a href="{auth_url}" class="button">Connect Spotify</a>
        </body>
        </html>
    '''

@app.route('/reauth', methods=['POST'])
def reauth():
    """Handle reauthorization request"""
    if clear_auth():
        return redirect('/')
    return 'Failed to clear authorization', 500

@app.route('/callback')
def callback():
    logger.info("Callback received from Spotify")
    code = request.args.get('code')
    auth_manager = SpotifyOAuth(
        scope='user-read-playback-state user-modify-playback-state',
        open_browser=False,
        show_dialog=True  # Always show dialog for account selection
    )
    
    try:
        # Get tokens from Spotify (spotipy will handle caching)
        auth_manager.get_access_token(code)
        logger.info("Successfully obtained access token")
    except Exception as e:
        logger.error(f"Error getting access token: {e}")
        return "Failed to authenticate with Spotify", 500
    
    return '''
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; max-width: 600px; margin: 40px auto; padding: 0 20px; text-align: center; }
                h1 { color: #1DB954; }
            </style>
        </head>
        <body>
            <h1>Setup Complete! ✓</h1>
            <p>Your SpotifyMatrix has been authenticated.</p>
            <p>You can now close this window and enjoy your music visualization!</p>
            <p>To switch accounts later, just visit this page again.</p>
            <script>
                setTimeout(function() {
                    window.close();
                }, 5000);
            </script>
        </body>
        </html>
    '''

if __name__ == '__main__':
    ip_address = get_local_ip()
    logger.info(f"Starting auth server on {ip_address}:{AUTH_SERVER_PORT}")
    print("\n" + "="*50)
    print(f"SpotifyMatrix Auth Server Running!")
    print(f"To authenticate Spotify, visit:")
    print(f"http://{ip_address}:{AUTH_SERVER_PORT}")
    print("="*50 + "\n")
    app.run(host='0.0.0.0', port=AUTH_SERVER_PORT) 