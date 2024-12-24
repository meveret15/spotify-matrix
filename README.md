# SpotifyMatrix

Display your currently playing Spotify album artwork on a 64x64 RGB LED Matrix. Features a colorful startup animation, smooth transitions between album art, and an easy web interface for account management.

## Features
- 🎵 Real-time Spotify album art display
- 🌈 Rainbow 3D text animations
- 🖼️ Smooth fade transitions between artwork
- 🔄 Easy account switching via web interface
- 🚀 Automatic startup on boot
- 📱 Fully headless operation
- 🔒 Secure token handling
- 📊 Automatic log management

## Hardware Requirements
- Raspberry Pi Zero 2W (or Pi 4)
- Adafruit RGB Matrix HAT + RTC
- 64x64 RGB LED Matrix Panel
- 5V 4A Power Supply for Matrix
- MicroSD Card (8GB+)

### Hardware Assembly
The Adafruit RGB Matrix HAT requires some modifications for optimal performance:

1. **PWM Sound Mod** (Required):
   - Solder a jumper wire between GPIO18 and GPIO4
   - This enables proper PWM control and reduces flickering

2. **Clock Speed Mod** (Required):
   - On the bottom of the HAT, solder the middle pad of the E0 jumper to pad 8
   - This sets the correct clock speed for stable operation

Refer to [Adafruit's RGB Matrix HAT guide](https://learn.adafruit.com/adafruit-rgb-matrix-plus-real-time-clock-hat-for-raspberry-pi/assembly) for detailed soldering instructions.

## Initial Setup

### 1. Prepare the Raspberry Pi
1. Download and install [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. Insert your SD card and open Raspberry Pi Imager
3. Click "CHOOSE OS" and select "Raspberry Pi OS Lite (64-bit)"
4. Click "CHOOSE STORAGE" and select your SD card
5. Click the ⚙️ gear icon to open advanced options:
   - Enable SSH
   - Set username and password
   - Configure WiFi
   - Set your locale settings
6. Click "SAVE" and then "WRITE"
7. Insert the SD card into your Pi and power it on
8. Find your Pi on the network and SSH in:
   ```bash
   ssh your_username@raspberrypi.local
   ```

### 2. Install System Dependencies
```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install required packages
sudo apt-get install -y git python3-dev python3-pip python3-venv libopenjp2-7 python3-pillow python3-setuptools
```

### 3. Install SpotifyMatrix
```bash
# Clone the repository
cd ~
git clone https://github.com/YOUR_USERNAME/spotify-matrix.git
cd spotify-matrix

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements (Flask, Spotipy, Pillow, etc.)
pip install -r requirements.txt
```

### 4. Install RGB Matrix Library
```bash
# Download and run Adafruit's installer script inside the project directory
cd ~/spotify-matrix
curl https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/main/rgb-matrix.sh > rgb-matrix.sh
sudo bash rgb-matrix.sh

# During installation:
# 1. Choose "Quality" (option 2) when prompted
# 2. Select "Yes" to update the sysclock
# 3. Choose "Yes" to activate realtime permissions
# 4. Reboot when prompted
```

After reboot, SSH back in and reactivate the virtual environment:
```bash
cd ~/spotify-matrix
source venv/bin/activate
```

### 5. Configure Services
```bash
# Copy service files
sudo cp spotify_auth.service /etc/systemd/system/
sudo cp spotify_display.service /etc/systemd/system/

# Edit service files to replace 'mever' with your username
sudo sed -i "s/mever/$USER/g" /etc/systemd/system/spotify_auth.service
sudo sed -i "s/mever/$USER/g" /etc/systemd/system/spotify_display.service

# Enable services
sudo systemctl enable spotify_auth.service spotify_display.service

# Start services
sudo systemctl start spotify_auth.service spotify_display.service
```

## Usage

### First-Time Setup
1. After starting the services, the matrix will display:
   - Rainbow "SPOTLIGHT" animation
   - The setup URL (IP address and port)
2. Visit the displayed URL in your web browser
3. Click "Connect Spotify" and authorize your account
4. Once authenticated, the matrix will automatically display your current Spotify album artwork

### Switching Spotify Accounts
1. Visit the same setup URL shown during first-time setup
2. Click "Switch Spotify Account"
3. Authorize the new account

### Troubleshooting

#### Check Service Status
```bash
# Check auth server status
sudo systemctl status spotify_auth.service

# Check display service status
sudo systemctl status spotify_display.service

# View logs
tail -f logs/display.log
tail -f logs/auth.log
tail -f logs/spotify.log
```

#### Common Issues
- **No Display**: Check matrix power supply and HAT connection
- **No Album Art**: Ensure Spotify is playing on any device
- **Auth Issues**: Try clearing auth by visiting the setup URL
- **Matrix Flicker**: 
  - Ensure quality power supply (5V 4A minimum)
  - Verify PWM and clock speed mods are properly soldered
  - Check HAT is firmly seated on GPIO pins

## Technical Details

### Service Architecture
- `spotify_auth.service`: Runs the authentication web server
- `spotify_display.service`: Manages the LED matrix display
- Both services run as root (required for hardware access)
- Automatic restart on failure

### File Structure
```
spotify-matrix/
├── config.py                # Configuration and settings
├── display_manager.py       # LED matrix control
├── spotify_client.py        # Spotify API interface
├── spotify_auth_server.py   # Auth web server
├── spotify_display_main.py  # Main display program
├── utils/
│   ├── logger.py           # Logging configuration
│   └── network.py          # Network utilities
├── logs/                   # Rotating log files
│   ├── display.log
│   ├── auth.log
│   ├── spotify.log
│   └── network.log
├── .cache                  # Spotify authentication token (managed by Spotipy)
├── rpi-rgb-led-matrix/    # RGB Matrix library
└── requirements.txt        # Python dependencies
```

### Log Management
- Automatic log rotation for all log files:
  - `display.log`: Matrix display operations
  - `auth.log`: Authentication server events
  - `spotify.log`: Spotify API interactions
  - `network.log`: Network connectivity
- Each log limited to 1MB with 3 backups
- Old logs automatically deleted

## Future Improvements
- Automated WiFi setup interface for fully headless operation
- Web-based matrix configuration (brightness, rotation)
- Additional display effects and transitions
- Support for other music services
