import time
import math
import datetime
from pymycobot import MyCobot280

# 1. Setup connection
mc = MyCobot280('/dev/ttyUSB0', 115200)
time.sleep(0.1)

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

print(f"{datetime.datetime.now()} Moving to starting position...")
# Move to glassHeight mm above the stirring height to enter the glass safely
mc.send_coords([center_x + radius, center_y, center_z + glassHeight, rx, ry, rz], 50, 1)


# Wait for physical travel time
print(f"{datetime.datetime.now()} Traveling to glass...")
time.sleep(3) 

# Actual wait at the position
print(f"{datetime.datetime.now()} Arrived. Waiting for 5 seconds...")
time.sleep(5)

print(f"{datetime.datetime.now()} Starting to stir!")
# Stirring loop (10 circles)
for i in range(10):
    for degree in range(0, 360, 20): # Move every 20 degrees
        angle = math.radians(degree)
        
        # Calculate X and Y for the circle
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        
        # Send the command
        mc.send_coords([x, y, center_z, rx, ry, rz], speed, 1)
        time.sleep(0.05)

print(f"{datetime.datetime.now()} Stirring finished. Centering and lifting...")
# Lift to 250.0mm height (clears your 150mm glass)
mc.send_coords([center_x + radius, center_y, center_z + glassHeight, rx, ry, rz], 50, 1)
time.sleep(2)

print(f"{datetime.datetime.now()} Moving to Park position (upright)...")
# Send the robot to its upright "Home" position
mc.send_angles([0, 0, 0, 0, 0, 0], 40)
time.sleep(3)

print(f"{datetime.datetime.now()} Done stirring! Arm is parked and powered.")
# mc.release_all_servos()  # Removed to prevent the arm from falling
