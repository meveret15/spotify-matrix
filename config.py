from rgbmatrix import RGBMatrixOptions

def get_matrix_options():
    """Get standard matrix configuration"""
    options = RGBMatrixOptions()
    options.rows = 64
    options.cols = 64
    options.chain_length = 1
    options.parallel = 1
    options.hardware_mapping = 'adafruit-hat'
    options.brightness = 70
    options.gpio_slowdown = 4
    return options

# Spotify configuration
SPOTIPY_CLIENT_ID = 'e41bd5086b4942aaa474ecdb3e443114'
SPOTIPY_CLIENT_SECRET = '567e3e77940544c9a0d1163fe6c99020'
REDIRECT_URI = 'http://192.168.1.145:8080/spotify-callback'

# WiFi configuration
WIFI_SETUP_SSID = "SpotlightSetup"
WIFI_SETUP_PASSWORD = "spotlightsetup"
WIFI_CONFIG_PATH = '/etc/wpa_supplicant/wpa_supplicant.conf'
HOSTAPD_CONFIG_PATH = '/etc/hostapd/hostapd.conf'
DNSMASQ_CONFIG_PATH = '/etc/dnsmasq.conf'