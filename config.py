import os
import socket
import netifaces

def get_local_ip():
    """Get IP address of the Pi on the local network (192.168.*)"""
    # First try the wlan0 interface
    try:
        addrs = netifaces.ifaddresses('wlan0')
        if netifaces.AF_INET in addrs:
            for addr in addrs[netifaces.AF_INET]:
                ip = addr['addr']
                if ip.startswith('192.168.'):
                    return ip
    except:
        pass

    # If not found, try all interfaces
    for interface in netifaces.interfaces():
        try:
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    ip = addr['addr']
                    if ip.startswith('192.168.'):
                        return ip
        except:
            continue

    # If no 192.168.* address found, try any non-localhost address
    for interface in netifaces.interfaces():
        try:
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    ip = addr['addr']
                    if not ip.startswith('127.'):
                        return ip
        except:
            continue

    return None

# Application paths
APP_NAME = "spotify-matrix"
APP_AUTHOR = "mever"

# Use local directories instead of system-wide ones
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, 'cache')
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# Ensure directories exist with proper permissions
os.makedirs(CACHE_DIR, mode=0o777, exist_ok=True)
os.makedirs(LOG_DIR, mode=0o777, exist_ok=True)

# Server configuration
AUTH_SERVER_PORT = 8080

# Matrix configuration
def get_matrix_options():
    return {
        "rows": 64,
        "cols": 64,
        "hardware_mapping": "adafruit-hat-pwm",
        "brightness": 70,
    }

# Spotify configuration
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "e41bd5086b4942aaa474ecdb3e443114")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "567e3e77940544c9a0d1163fe6c99020")
SPOTIFY_REDIRECT_URI = f"http://{get_local_ip()}:{AUTH_SERVER_PORT}/callback" if get_local_ip() else f"http://localhost:{AUTH_SERVER_PORT}/callback"

# Network status check
NETWORK_CHECK_URL = "https://api.spotify.com"  # Used to verify internet connectivity