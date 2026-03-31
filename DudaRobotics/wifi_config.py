# wifi_config.py — read/change WiFi on myCobot 280 M5 via USB serial
#
# Usage (from inside Docker):
#   python3 /ros2_ws/src/mycobot_ros2/DudaRobotics/wifi_config.py          # read only
#   python3 /ros2_ws/src/mycobot_ros2/DudaRobotics/wifi_config.py --set    # read + set new

import sys
import time
from pymycobot import MyCobot280

# --- Connection via USB serial ---
SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 115200

# --- New WiFi credentials (only used with --set) ---
NEW_SSID     = 'MyCobotWiFi2.4G'
NEW_PASSWORD = '12345678'

print(f"Connecting to myCobot on {SERIAL_PORT}...")
mc = MyCobot280(SERIAL_PORT, BAUD_RATE)
time.sleep(0.5)

# Read current WiFi settings
print("Current WiFi config:", mc.get_ssid_pwd())

if '--set' in sys.argv:
    print(f"\nSetting WiFi SSID={NEW_SSID} ...")
    mc.set_ssid_pwd(NEW_SSID, NEW_PASSWORD)
    time.sleep(1)

    # Verify
    print("Updated WiFi config:", mc.get_ssid_pwd())
    print("\nDone. Reboot the myCobot for the new WiFi settings to take effect.")
else:
    print("\nTo change WiFi, run with --set flag:")
    print(f"  python3 wifi_config.py --set")


