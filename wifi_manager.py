import subprocess
import os
import time
from flask import Flask, request, render_template_string
import threading
from utils.logger import setup_logger
from config import (
    WIFI_SETUP_SSID,
    WIFI_SETUP_PASSWORD,
    WIFI_CONFIG_PATH,
    HOSTAPD_CONFIG_PATH,
    DNSMASQ_CONFIG_PATH
)

logger = setup_logger('wifi', 'wifi.log')

class WifiManager:
    def __init__(self, spotify_client, display=None):
        logger.info("Initializing WifiManager")
        self.app = Flask(__name__)
        self.spotify_client = spotify_client
        self.display = display
        
        # Setup routes
        self._setup_routes()
        
        # Initialize AP mode if needed
        if not self.is_connected():
            logger.info("No WiFi connection, starting AP mode")
            self._setup_ap_mode()
    
    def _setup_ap_mode(self):
        """Setup Access Point mode with retry logic"""
        try:
            logger.info("Setting up AP mode")
            
            # Save current network configuration for recovery
            self._backup_network_config()
            
            # Start recovery timer in a separate thread
            recovery_thread = threading.Thread(target=self._recovery_timer)
            recovery_thread.daemon = True
            recovery_thread.start()
            
            # Force disconnect from any network
            subprocess.run(['sudo', 'wpa_cli', '-i', 'wlan0', 'disconnect'])
            subprocess.run(['sudo', 'ip', 'link', 'set', 'wlan0', 'down'])
            
            # Stop all networking services
            subprocess.run(['sudo', 'systemctl', 'stop', 'wpa_supplicant'])
            subprocess.run(['sudo', 'systemctl', 'stop', 'dhcpcd'])
            subprocess.run(['sudo', 'systemctl', 'stop', 'hostapd'])
            subprocess.run(['sudo', 'systemctl', 'stop', 'dnsmasq'])
            
            # Configure network interface
            subprocess.run(['sudo', 'ip', 'addr', 'flush', 'dev', 'wlan0'])
            subprocess.run(['sudo', 'ip', 'link', 'set', 'wlan0', 'up'])
            subprocess.run(['sudo', 'ip', 'addr', 'add', '192.168.4.1/24', 'dev', 'wlan0'])
            
            # Configure hostapd
            with open(HOSTAPD_CONFIG_PATH, 'w') as f:
                f.write(f"""
interface=wlan0
driver=nl80211
ssid={WIFI_SETUP_SSID}
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase={WIFI_SETUP_PASSWORD}
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
country_code=US
""".strip())
            
            # Configure dnsmasq
            with open(DNSMASQ_CONFIG_PATH, 'w') as f:
                f.write("""
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
address=/#/192.168.4.1
""".strip())
            
            # Start services
            subprocess.run(['sudo', 'systemctl', 'start', 'hostapd'])
            time.sleep(2)  # Give hostapd time to start
            subprocess.run(['sudo', 'systemctl', 'start', 'dnsmasq'])
            
            logger.info("AP mode setup completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup AP mode: {str(e)}")
            self._restore_network_config()
            return False

    def _recovery_timer(self):
        """Revert to normal WiFi mode if no one connects within 5 minutes"""
        RECOVERY_TIMEOUT = 300  # 5 minutes
        start_time = time.time()
        
        while time.time() - start_time < RECOVERY_TIMEOUT:
            # Check if anyone has connected to our AP
            try:
                leases = open('/var/lib/misc/dnsmasq.leases').read()
                if leases.strip():  # If anyone has connected
                    return
            except:
                pass
            time.sleep(5)
        
        logger.info("Recovery timeout reached. Reverting to normal WiFi mode")
        self._restore_network_config()

    def _backup_network_config(self):
        """Backup current network configuration"""
        try:
            if os.path.exists(WIFI_CONFIG_PATH):
                os.system(f'cp {WIFI_CONFIG_PATH} {WIFI_CONFIG_PATH}.backup')
        except Exception as e:
            logger.error(f"Failed to backup network config: {str(e)}")

    def _restore_network_config(self):
        """Restore previous network configuration"""
        try:
            if os.path.exists(f'{WIFI_CONFIG_PATH}.backup'):
                os.system(f'cp {WIFI_CONFIG_PATH}.backup {WIFI_CONFIG_PATH}')
                self._stop_ap_mode()
                self._restart_networking()
        except Exception as e:
            logger.error(f"Failed to restore network config: {str(e)}")

    def _cleanup_network_processes(self):
        """Clean up any existing network processes"""
        try:
            # Stop services
            services = ['hostapd', 'dnsmasq', 'wpa_supplicant', 'dhcpcd']
            for service in services:
                subprocess.run(['sudo', 'systemctl', 'stop', service], stderr=subprocess.PIPE)
                subprocess.run(['sudo', 'killall', '-9', service], stderr=subprocess.PIPE)
            
            # Clean up any existing pid files
            pid_files = ['/var/run/hostapd.pid', '/var/run/dnsmasq.pid']
            for pid_file in pid_files:
                if os.path.exists(pid_file):
                    os.remove(pid_file)
        except Exception as e:
            logger.warning(f"Cleanup warning (non-fatal): {str(e)}")

    def _verify_ap_mode(self):
        """Verify AP mode is running correctly"""
        try:
            # Check hostapd is running
            hostapd_output = subprocess.check_output(['ps', 'aux']).decode()
            if 'hostapd' not in hostapd_output:
                return False
            
            # Check interface is configured
            ifconfig_output = subprocess.check_output(['ifconfig', 'wlan0']).decode()
            if '192.168.4.1' not in ifconfig_output:
                return False
            
            return True
        except Exception as e:
            logger.error(f"AP verification failed: {str(e)}")
            return False

    def _setup_routes(self):
        """Setup routes for the Flask app"""
        @self.app.route('/', defaults={'path': ''})
        @self.app.route('/<path:path>')
        def setup_page(path):
            # Captive portal detection
            user_agent = request.headers.get('User-Agent', '').lower()
            if 'captiveportal' in user_agent or 'captivenetworksupport' in user_agent:
                return '', 204
            
            spotify_auth_url = self.spotify_client.get_auth_url()
            networks = self._scan_networks()
            return render_template_string("""
            <html>
                <head>
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <style>
                        body { 
                            font-family: Arial; 
                            max-width: 800px; 
                            margin: 0 auto; 
                            padding: 20px;
                        }
                        .error { color: red; }
                        .success { color: green; }
                        .status { margin: 10px 0; }
                        select, input { 
                            width: 100%;
                            padding: 8px;
                            margin: 5px 0;
                        }
                        button {
                            background: #4CAF50;
                            color: white;
                            padding: 10px;
                            border: none;
                            border-radius: 4px;
                            cursor: pointer;
                        }
                    </style>
                    <script>
                        function checkStatus() {
                            fetch('/status')
                                .then(response => response.json())
                                .then(data => {
                                    document.getElementById('status').innerHTML = data.message;
                                    if (data.success) {
                                        document.getElementById('spotify-section').style.display = 'block';
                                    }
                                });
                        }
                        setInterval(checkStatus, 5000);
                    </script>
                </head>
                <body>
                    <h1>Spotlight Setup</h1>
                    
                    <h2>WiFi Setup</h2>
                    <form action="/connect" method="POST" id="wifi-form">
                        <select name="ssid" required>
                            <option value="">Select WiFi Network</option>
                            {% for network in networks %}
                                <option value="{{ network }}">{{ network }}</option>
                            {% endfor %}
                        </select>
                        <input type="password" name="password" placeholder="Password" required>
                        <button type="submit">Connect</button>
                    </form>
                    
                    <div id="status" class="status"></div>
                    
                    <div id="spotify-section" style="display:none">
                        <h2>Spotify Setup</h2>
                        <a href="{{ spotify_url }}" class="button">Connect Spotify Account</a>
                    </div>
                </body>
            </html>
            """, spotify_url=spotify_auth_url, networks=networks)

        @self.app.route('/status')
        def status():
            if self.is_connected():
                return {"success": True, "message": "Connected to WiFi"}
            return {"success": False, "message": "Waiting for connection..."}

        @self.app.route('/connect', methods=['POST'])
        def connect():
            ssid = request.form.get('ssid')
            password = request.form.get('password')
            
            logger.info(f"Attempting to connect to WiFi network: {ssid}")
            if self.display:
                self.display.show_text(f"Connecting to\n{ssid}")
                
            if self._configure_wifi(ssid, password):
                return "Successfully connected to WiFi. Please proceed with Spotify setup."
            else:
                return "Failed to connect to WiFi. Please try again.", 400

        @self.app.route('/spotify-callback')
        def spotify_callback():
            code = request.args.get('code')
            if code and self.spotify_client.handle_auth_callback(code):
                if self.display:
                    self.display.show_text("Starting\nDisplay...")
                # Start display in a new thread
                threading.Thread(target=self._start_display).start()
                return "Spotify connected successfully! You can close this page."
            return "Failed to connect Spotify. Please try again."

    def _start_display(self):
        """Start the display after a short delay"""
        time.sleep(2)  # Give time for the success message
        from main import main as run_display
        run_display()

    def test_setup(self, host='0.0.0.0', port=8080):
        """Test version that doesn't reconfigure WiFi"""
        print("Running in TEST MODE - no WiFi reconfiguration")
        self.app.run(host=host, port=port)

    def is_connected(self):
        """Check if we're connected to WiFi"""
        try:
            # Check if wlan0 has an IP address
            result = subprocess.check_output(['iwgetid']).decode('utf-8')
            return bool(result.strip())
        except:
            return False

    def _configure_wifi(self, ssid, password):
        """Configure WiFi connection with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Configuring WiFi for SSID: {ssid} (attempt {attempt + 1}/{max_retries})")
                
                # Write configuration
                self._write_wifi_config(ssid, password)
                
                # Stop AP mode and restart networking
                self._stop_ap_mode()
                self._restart_networking()
                
                # Wait for connection with progress updates
                if self._wait_for_connection():
                    logger.info("Successfully connected to WiFi")
                    return True
                    
                logger.error("Connection timeout")
                
            except Exception as e:
                logger.error(f"WiFi configuration failed (attempt {attempt + 1}): {str(e)}")
            
            if attempt < max_retries - 1:
                logger.info("Retrying WiFi configuration...")
                time.sleep(5)
                if self.display:
                    self.display.show_text(f"Retrying...\n{attempt + 2}/{max_retries}")
        
        # If all retries failed, go back to AP mode
        logger.error("Failed to configure WiFi after all retries")
        if self.display:
            self.display.show_text("WiFi Failed\nReturning to\nSetup Mode")
        self._setup_ap_mode()
        return False

    def _wait_for_connection(self, timeout=30):
        """Wait for WiFi connection with progress updates"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_connected():
                return True
            
            # Update progress every 5 seconds
            if int(time.time() - start_time) % 5 == 0:
                progress = int((time.time() - start_time) / timeout * 100)
                logger.info(f"Waiting for connection... {progress}%")
                if self.display:
                    self.display.show_text(f"Connecting\n{progress}%")
            
            time.sleep(1)
        return False

    def _write_wifi_config(self, ssid, password):
        """Write WiFi configuration with proper error handling"""
        try:
            wpa_config = f"""
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=US

network={{
    ssid="{ssid}"
    psk="{password}"
    key_mgmt=WPA-PSK
}}
"""
            # Write to temporary file first
            temp_config = f"{WIFI_CONFIG_PATH}.tmp"
            with open(temp_config, 'w') as f:
                f.write(wpa_config)
            
            # Set permissions
            os.chmod(temp_config, 0o600)
            
            # Move to final location
            os.rename(temp_config, WIFI_CONFIG_PATH)
            
        except Exception as e:
            logger.error(f"Failed to write WiFi config: {str(e)}")
            raise

    def _stop_ap_mode(self):
        """Stop Access Point mode"""
        logger.info("Stopping AP mode")
        try:
            subprocess.run(['sudo', 'killall', 'hostapd'])
            subprocess.run(['sudo', 'killall', 'dnsmasq'])
        except Exception as e:
            logger.error(f"Error stopping AP mode: {str(e)}")

    def _restart_networking(self):
        """Restart networking services"""
        logger.info("Restarting network services")
        try:
            subprocess.run(['sudo', 'systemctl', 'restart', 'dhcpcd'])
            subprocess.run(['sudo', 'systemctl', 'restart', 'wpa_supplicant'])
        except Exception as e:
            logger.error(f"Error restarting network services: {str(e)}")

    def start_setup(self, host='192.168.4.1', port=8080):
        """Start the setup process"""
        logger.info(f"Starting setup server on {host}:{port}")
        if self.display:
            self.display.show_text("Connect to:\nSpotlightSetup\nPass: spotlightsetup")
        self.app.run(host=host, port=port)

    def _scan_networks(self):
        """Scan for available WiFi networks"""
        try:
            output = subprocess.check_output(['sudo', 'iwlist', 'wlan0', 'scan'])
            networks = []
            for line in output.decode('utf-8').split('\n'):
                if 'ESSID:' in line:
                    network = line.split('ESSID:"')[1].split('"')[0]
                    if network:  # Only add non-empty SSIDs
                        networks.append(network)
            return sorted(list(set(networks)))  # Remove duplicates and sort
        except Exception as e:
            logger.error(f"Failed to scan networks: {str(e)}")
            return []