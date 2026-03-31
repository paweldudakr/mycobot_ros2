import time
import math
import datetime
import argparse

def log(msg):
    print(f"{datetime.datetime.now()} {msg}")

# --- Connection mode ---
# USB serial: reliable for both read and write (default)
# WiFi: requires M5Stack to be in WLAN Server mode (set via M5Stack screen).
#   WiFi is write-only (no readback). Use --wifi flag.
parser = argparse.ArgumentParser(description='MyCobot 280 stirring script')
parser.add_argument('--wifi', action='store_true',
                    help='Use WiFi instead of USB serial (M5Stack must be in WLAN Server mode)')
parser.add_argument('--ip', default='192.168.6.57', help='Robot WiFi IP (default: 192.168.6.57)')
parser.add_argument('--port', type=int, default=9000, help='Robot WiFi port (default: 9000)')
parser.add_argument('--serial', default='/dev/ttyUSB0', help='USB serial port (default: /dev/ttyUSB0)')
args = parser.parse_args()

if args.wifi:
    from mycobot_wifi import MyCobotWiFi
    log(f"Connecting via WiFi ({args.ip}:{args.port})...")
    mc = MyCobotWiFi(args.ip, args.port)
else:
    from pymycobot import MyCobot280
    log(f"Connecting via USB serial ({args.serial})...")
    mc = MyCobot280(args.serial, 115200)
    time.sleep(0.5)

# 2. Settings for the "Stir"
# You might need to adjust these coordinates based on where your glass is!
# [4.0, -250.1, 141.7, 179.31, -0.72, -165.84]
# [-14.5, -229.6, 245.0, -177.66, 4.13, -177.88]
center_x = -14.5   # Forward/Backward
center_y = -229.6     # Left/Right
center_z = 185.0   # Height (Bottom of the glass)

# GET YOUR CURRENT ROTATION (the last 3 numbers from get_coords)
# Usually for pointing down it is [-180, 0, 0] or [0, 180, 0]
rx, ry, rz = -177.66, 4.13, -177.88

radius = 10.0      # How wide is the circle?
speed = 50

glassHeight = 60.0

log("Moving to starting position...")
mc.send_coords([center_x + radius, center_y, center_z + glassHeight, rx, ry, rz], 50, 1)

log("Traveling to glass...")
time.sleep(3) 

log("Arrived. Waiting for 5 seconds...")
time.sleep(5)

log("Starting to stir!")
# Stirring loop (10 circles)
for i in range(10):
    for degree in range(0, 360, 20):
        angle = math.radians(degree)
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)

        mc.send_coords([x, y, center_z, rx, ry, rz], speed, 1)
        time.sleep(0.05)
    log(f"  Circle {i+1}/10 done")

log("Stirring finished. Centering and lifting...")
mc.send_coords([center_x + radius, center_y, center_z + glassHeight, rx, ry, rz], 50, 1)
time.sleep(2)

log("Moving to Park position (upright)...")
mc.send_angles([0, 0, 0, 0, 0, 0], 40)
time.sleep(3)

log("Done stirring! Arm is parked and powered.")
