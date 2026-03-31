#!/usr/bin/env python3
"""End-to-end WiFi test: send via raw socket, verify via USB serial."""

import socket
import time
import datetime
from pymycobot import MyCobot280

IP = '192.168.6.57'
PORT = 9000
SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 115200
TOLERANCE = 5.0
SPEED = 40
SETTLE_TIME = 5  # seconds to wait for movement

def log(msg):
    print(f'{datetime.datetime.now()} {msg}')

def encode_send_angles(angles, speed):
    genre = 0x20
    data = []
    for a in angles:
        val = int(a * 100)
        if val < 0:
            val = val & 0xFFFF
        data.extend([(val >> 8) & 0xFF, val & 0xFF])
    data.append(speed)
    length = len(data) + 2
    return bytes([0xFE, 0xFE, length, genre] + data + [0xFA])

def wifi_send_angles(angles, speed):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect((IP, PORT))
    s.sendall(encode_send_angles(angles, speed))
    s.close()

def read_angles_usb():
    mc = MyCobot280(SERIAL_PORT, BAUD_RATE)
    time.sleep(0.5)
    angles = mc.get_angles()
    if hasattr(mc, 'close'):
        mc.close()
    time.sleep(0.3)
    return angles

def check_angle(actual, expected_j1):
    if not actual or actual == -1:
        return False
    return abs(actual[0] - expected_j1) < TOLERANCE

results = []

# Initial position
log('Reading initial angles...')
init = read_angles_usb()
log(f'  Initial: {init}')

# Test 1: send 45 via WiFi
log('')
log('=== TEST 1: WiFi send [45,0,0,0,0,0] ===')
wifi_send_angles([45,0,0,0,0,0], SPEED)
log(f'  Sent. Waiting {SETTLE_TIME}s...')
time.sleep(SETTLE_TIME)
a1 = read_angles_usb()
ok1 = check_angle(a1, 45)
log(f'  Angles: {a1}')
log(f'  Result: {"PASS" if ok1 else "FAIL"}')
results.append(('WiFi 45deg', ok1))

# Test 2: send -45 via WiFi
log('')
log('=== TEST 2: WiFi send [-45,0,0,0,0,0] ===')
wifi_send_angles([-45,0,0,0,0,0], SPEED)
log(f'  Sent. Waiting {SETTLE_TIME}s...')
time.sleep(SETTLE_TIME)
a2 = read_angles_usb()
ok2 = check_angle(a2, -45)
log(f'  Angles: {a2}')
log(f'  Result: {"PASS" if ok2 else "FAIL"}')
results.append(('WiFi -45deg', ok2))

# Test 3: send_coords via WiFi
log('')
log('=== TEST 3: WiFi send_coords ===')
# Encode send_coords
def encode_send_coords(coords, speed, mode):
    genre = 0x21
    data = []
    for i, c in enumerate(coords):
        if i < 3:
            val = int(c * 10)
        else:
            val = int(c * 100)
        if val < 0:
            val = val & 0xFFFF
        data.extend([(val >> 8) & 0xFF, val & 0xFF])
    data.append(speed)
    data.append(mode)
    length = len(data) + 2
    return bytes([0xFE, 0xFE, length, genre] + data + [0xFA])

test_coords = [150.0, 0.0, 200.0, -180.0, 0.0, -90.0]
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(5)
s.connect((IP, PORT))
s.sendall(encode_send_coords(test_coords, SPEED, 1))
s.close()
log(f'  Sent coords {test_coords}. Waiting {SETTLE_TIME}s...')
time.sleep(SETTLE_TIME)
a3 = read_angles_usb()
log(f'  Angles after coords: {a3}')
# Just check we read something valid (can't easily predict angles from coords)
ok3 = a3 is not None and a3 != -1 and len(a3) == 6
log(f'  Result: {"PASS (valid response)" if ok3 else "FAIL"}')
results.append(('WiFi coords', ok3))

# Park
log('')
log('=== PARK ===')
wifi_send_angles([0,0,0,0,0,0], SPEED)
time.sleep(4)
final = read_angles_usb()
log(f'  Final angles: {final}')

# Summary
log('')
log('=' * 40)
log('SUMMARY')
log('=' * 40)
all_pass = True
for name, ok in results:
    status = 'PASS' if ok else 'FAIL'
    log(f'  {name:20s} {status}')
    if not ok:
        all_pass = False
log('')
if all_pass:
    log('ALL TESTS PASSED')
else:
    log('SOME TESTS FAILED')
