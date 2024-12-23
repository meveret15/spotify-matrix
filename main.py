#!/usr/bin/env python3
import os
import sys
import time
import json
import requests
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from display_manager import DisplayManager
from spotify_client import SpotifyClient
from flask import Flask, request
from utils.logger import setup_logger
from config import (
    get_matrix_options,
    CREDENTIALS_FILE,
    NETWORK_CHECK_URL
)

# Setup logging
logger = setup_logger('main', 'main.log')
app = Flask(__name__)
matrix = None
display = None
spotify = None

def check_internet():
    """Check if we have internet connectivity"""
    try:
        requests.get(NETWORK_CHECK_URL, timeout=5)
        return True
    except:
        return False

def check_credentials():
    """Check if we have stored Spotify credentials"""
    try:
        if os.path.exists(CREDENTIALS_FILE):
            with open(CREDENTIALS_FILE, 'r') as f:
                creds = json.load(f)
                return all(k in creds for k in ['access_token', 'refresh_token'])
        return False
    except:
        return False

def init_hardware():
    """Initialize the LED matrix"""
    global matrix, display
    try:
        options = RGBMatrixOptions()
        matrix_config = get_matrix_options()
        for key, value in matrix_config.items():
            setattr(options, key, value)
        
        matrix = RGBMatrix(options=options)
        display = DisplayManager(matrix)
        return True
    except Exception as e:
        logger.error(f"Failed to initialize hardware: {e}")
        return False

def run_setup_mode():
    """Run the setup web server for Spotify authorization"""
    global spotify
    
    @app.route('/')
    def setup_page():
        auth_url = spotify.get_auth_url() if spotify else ""
        return f"""
        <html>
            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {{ font-family: Arial; max-width: 800px; margin: 0 auto; padding: 20px; }}
                    .button {{ 
                        display: inline-block;
                        padding: 10px 20px;
                        background: #1DB954;
                        color: white;
                        text-decoration: none;
                        border-radius: 20px;
                        margin: 10px 0;
                    }}
                </style>
            </head>
            <body>
                <h1>Spotify Matrix Setup</h1>
                <p>To configure WiFi, visit the <a href="http://10.3.141.1">RaspAP dashboard</a></p>
                <p>Once connected to WiFi, click below to connect your Spotify account:</p>
                <a href="{auth_url}" class="button">Connect Spotify</a>
            </body>
        </html>
        """

    @app.route('/callback')
    def callback():
        code = request.args.get('code')
        if code and spotify:
            success = spotify.handle_auth_callback(code)
            if success:
                return """
                <h1>Setup Complete!</h1>
                <p>You can close this window. Your display will start showing album artwork shortly.</p>
                """
        return "Setup failed. Please try again."

    # Start the setup server
    app.run(host='0.0.0.0', port=8080)

def run_display_mode():
    """Run the main display loop"""
    global display, spotify
    
    # Show welcome message
    if display:
        display.show_text("SPOTIFY\nMATRIX")
    
    last_art_url = None
    while True:
        try:
            if not check_internet():
                display.show_text("NO\nINTERNET")
                time.sleep(5)
                continue
                
            current_track = spotify.get_current_track()
            if current_track and current_track.get('album_art_url'):
                if current_track['album_art_url'] != last_art_url:
                    display.show_album_art(current_track['album_art_url'])
                    last_art_url = current_track['album_art_url']
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Display loop error: {e}")
            if display:
                display.show_text("ERROR")
            time.sleep(5)

def main():
    """Main application entry point"""
    global spotify
    
    # Check if running as root
    if os.geteuid() != 0:
        sys.exit("Script must run as root. Please run with: sudo python main.py")
    
    # Initialize hardware
    if not init_hardware():
        sys.exit("Failed to initialize LED matrix")
    
    # Initialize Spotify client
    spotify = SpotifyClient()
    
    # Determine which mode to run in
    if not check_internet() or not check_credentials():
        logger.info("Entering setup mode")
        if display:
            display.show_text("SETUP\nMODE")
        run_setup_mode()
    else:
        logger.info("Entering display mode")
        run_display_mode()

if __name__ == "__main__":
    main()