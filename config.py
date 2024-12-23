import os
from platformdirs import user_config_dir

# Application paths
APP_NAME = "spotify-matrix"
CONFIG_DIR = user_config_dir(APP_NAME)
CREDENTIALS_FILE = os.path.join(CONFIG_DIR, "credentials.json")
LOG_DIR = "/var/log/spotlight"

# Ensure directories exist
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Matrix configuration
def get_matrix_options():
    return {
        "rows": 64,
        "cols": 64,
        "chain_length": 1,
        "parallel": 1,
        "hardware_mapping": "regular",
        "gpio_slowdown": 4,
        "brightness": 70
    }

# Spotify configuration
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "your_client_id_here")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "your_client_secret_here")
SPOTIFY_REDIRECT_URI = "http://localhost:8080/callback"

# Network status check
NETWORK_CHECK_URL = "https://api.spotify.com"  # Used to verify internet connectivity