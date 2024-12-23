import os
import netifaces

def get_local_ip():
    """Get IP address of the Pi on the local network"""
    # Try common interface names
    for interface in ['wlan0', 'eth0', 'wlan1', 'eth1']:
        try:
            if interface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    # Get the first IPv4 address that's not 127.0.0.1 or 10.*.*.*
                    for addr in addrs[netifaces.AF_INET]:
                        ip = addr['addr']
                        if not (ip.startswith('127.') or ip.startswith('10.')):
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

# Matrix configuration
def get_matrix_options():
    return {
        "rows": 64,
        "cols": 64,
        "chain_length": 1,
        "parallel": 1,
        "hardware_mapping": "adafruit-hat",
        "gpio_slowdown": 2,
        "brightness": 50,
        # Basic settings for stability
        "pwm_bits": 11,
        "show_refresh_rate": True
    }

# Spotify configuration
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "e41bd5086b4942aaa474ecdb3e443114")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "567e3e77940544c9a0d1163fe6c99020")
SPOTIFY_REDIRECT_URI = f"http://{get_local_ip()}:8080/callback" if get_local_ip() else "http://localhost:8080/callback"

# Network status check
NETWORK_CHECK_URL = "https://api.spotify.com"  # Used to verify internet connectivity