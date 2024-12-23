# Spotify Matrix Display

A Raspberry Pi project that displays your currently playing Spotify album artwork on an LED matrix display. This project is designed to work completely headlessly, allowing users to set it up without connecting a keyboard or monitor.

## Technical Setup (Development)

### Hardware Requirements
- Raspberry Pi (tested on Pi 4)
- RGB LED Matrix HAT
- RGB LED Matrix Panel (64x64)
- Power supply for both Pi and LED Matrix
- MicroSD card (8GB+ recommended)

### Software Requirements
- Raspberry Pi OS (Debian Bookworm or newer)
- Python 3.11+
- RaspAP for WiFi management
- Required Python packages (see requirements.txt)

### Initial Setup
1. Flash Raspberry Pi OS to your SD card
2. Enable SSH access
3. Connect to your Pi via SSH
4. Clone this repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/spotify-matrix.git
   cd spotify-matrix
   ```

### Installation Steps
1. Install system dependencies:
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3-dev python3-pillow python3-pip cython3
   ```

2. Install RaspAP for WiFi management:
   ```bash
   curl -sL https://install.raspap.com | bash
   ```

3. Install RGB Matrix library:
   ```bash
   cd rpi-rgb-led-matrix
   make
   cd bindings/python
   make build-python
   sudo make install-python
   cd ../../..
   ```

4. Set up Python environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

5. Install the service:
   ```bash
   sudo cp setup_spotlight.service /etc/systemd/system/
   sudo systemctl enable setup_spotlight
   sudo systemctl start setup_spotlight
   ```

### Development Notes
- The project uses RaspAP for WiFi management (default AP SSID: "raspi-webgui")
- Spotify credentials are stored securely in the config file
- The system automatically starts in setup mode if WiFi or Spotify auth is missing
- All logs are stored in /var/log/spotlight/

## User Guide

### First-Time Setup
1. Power on your Spotify Matrix Display
2. On your phone/computer, connect to the WiFi network "raspi-webgui"
   - Default password: "secret"
3. Open a web browser and go to http://10.3.141.1
4. Follow the on-screen instructions to:
   - Connect the device to your WiFi network
   - Authorize your Spotify account

### Normal Operation
- Once setup is complete, the display will automatically show your currently playing Spotify album artwork
- The device will automatically reconnect to your WiFi and Spotify on power cycles
- If either WiFi or Spotify connection is lost, it will automatically enter setup mode

### Troubleshooting
1. If the display shows nothing:
   - Check power connections
   - Look for the "raspi-webgui" WiFi network
2. If album art isn't updating:
   - Ensure Spotify is playing on any of your devices
   - Check your WiFi connection
3. To reset the device:
   - Hold the reset button for 10 seconds
   - The device will return to setup mode

### Safety Features
- The system maintains SSH access even in setup mode
- All configurations are backed up before modifications
- Automatic recovery if setup fails

## Technical Details
- WiFi management: RaspAP
- Display: rpi-rgb-led-matrix library
- Spotify integration: Spotipy library
- Web interface: Flask
- Service management: Systemd

## Contributing
Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License
This project is licensed under the MIT License - see the LICENSE file for details 