import subprocess
import os
import time
from flask import Flask, request
import threading
import json

class WifiManager:
    def __init__(self):
        self.app = Flask(__name__)
        self.config_file = '/etc/wpa_supplicant/wpa_supplicant.conf'
        self.hostapd_config = '/etc/hostapd/hostapd.conf'
        
    def is_connected(self):
        try:
            result = subprocess.run(['iwgetid'], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False

    def setup_ap(self):
        # Configure hostapd
        hostapd_conf = """
interface=wlan0
driver=nl80211
ssid=SpotlightSetup
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=spotlightsetup
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
"""
        with open(self.hostapd_config, 'w') as f:
            f.write(hostapd_conf)

        # Start AP
        subprocess.run(['systemctl', 'start', 'hostapd'])
        subprocess.run(['systemctl', 'start', 'dnsmasq'])

    def stop_ap(self):
        subprocess.run(['systemctl', 'stop', 'hostapd'])
        subprocess.run(['systemctl', 'stop', 'dnsmasq'])

    def setup_wifi(self):
        def run_flask():
            self.app.run(host='0.0.0.0', port=80)

        @self.app.route('/')
        def wifi_setup_page():
            return """
            <html>
                <body>
                    <h1>Spotlight WiFi Setup</h1>
                    <form action="/connect" method="POST">
                        <input type="text" name="ssid" placeholder="WiFi Name">
                        <input type="password" name="password" placeholder="Password">
                        <input type="submit" value="Connect">
                    </form>
                </body>
            </html>
            """

        @self.app.route('/connect', methods=['POST'])
        def connect_wifi():
            ssid = request.form['ssid']
            password = request.form['password']
            
            # Update wpa_supplicant.conf
            wpa_conf = f"""
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={{
    ssid="{ssid}"
    psk="{password}"
    key_mgmt=WPA-PSK
}}
"""
            with open(self.config_file, 'w') as f:
                f.write(wpa_conf)
            
            # Restart networking
            subprocess.run(['wpa_cli', '-i', 'wlan0', 'reconfigure'])
            return "Connected! You can close this page."

        # Start AP mode
        self.setup_ap()
        
        # Start Flask server in a thread
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()
        
        # Wait for connection
        while not self.is_connected():
            time.sleep(1)
        
        # Stop AP mode
        self.stop_ap()