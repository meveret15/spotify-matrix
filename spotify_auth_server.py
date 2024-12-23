from flask import Flask, redirect, request
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import netifaces
from config import (
    SPOTIFY_CLIENT_ID,
    SPOTIFY_CLIENT_SECRET,
    SPOTIFY_REDIRECT_URI
)

app = Flask(__name__)

def get_local_ip():
    # Get IP address of the Pi on the local network
    interfaces = netifaces.interfaces()
    for interface in interfaces:
        if interface.startswith('w'):  # wifi interface
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                return addrs[netifaces.AF_INET][0]['addr']
    return None

@app.route('/')
def index():
    auth_manager = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope='user-read-playback-state user-modify-playback-state',
        open_browser=False
    )
    
    try:
        if auth_manager.validate_token(auth_manager.get_cached_token()):
            return '<h1>Spotify already authenticated!</h1>'
    except:
        pass
    
    auth_url = auth_manager.get_authorize_url()
    return f'''
        <h1>Welcome to SpotifyMatrix!</h1>
        <p>Click the button below to authenticate with Spotify:</p>
        <a href="{auth_url}" style="display: inline-block; background-color: #1DB954; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">
            Connect Spotify
        </a>
    '''

@app.route('/callback')
def callback():
    code = request.args.get('code')
    auth_manager = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope='user-read-playback-state user-modify-playback-state',
        open_browser=False
    )
    
    # Get tokens from Spotify (spotipy will handle caching)
    auth_manager.get_access_token(code)
    
    return '''
        <h1>Setup Complete! ✓</h1>
        <p>Your SpotifyMatrix has been authenticated.</p>
        <p>You can now close this window and enjoy your music visualization!</p>
        <script>
            setTimeout(function() {
                window.close();
            }, 5000);
        </script>
    '''

if __name__ == '__main__':
    ip_address = get_local_ip()
    print("\n" + "="*50)
    print(f"SpotifyMatrix Auth Server Running!")
    print(f"To authenticate Spotify, visit:")
    print(f"http://{ip_address}:8080")
    print("="*50 + "\n")
    app.run(host='0.0.0.0', port=8080) 