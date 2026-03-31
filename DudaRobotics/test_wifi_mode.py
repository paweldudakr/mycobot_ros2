#!/usr/bin/env python3
"""Controlled WiFi mode test:
1. Switch to WiFi mode via USB
2. Close USB completely
3. Send ONE movement command via raw TCP socket
4. Wait for movement
5. Switch back to UART via USB
6. Read angles to verify
"""

import socket
import time
import datetime
from pymycobot import MyCobot280

IP = '192.168.6.57'
PORT = 9000
SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 115200

def log(msg):
    print(f'{datetime.datetime.now()} {msg}')

def encode_send_angles(angles, speed):
    genre = 0x20
    data = []
    for a in angles:
        val = int(a * 100)
        if val < 0:
            val = val + 0x10000
        data.extend([(val >> 8) & 0xFF, val & 0xFF])
    data.append(speed)
    length = len(data) + 2
    return bytes([0xFE, 0xFE, length, genre] + data + [0xFA])

# Step 1: Switch to WiFi mode via USB
log('Step 1: READ initial state via USB')
mc = MyCobot280(SERIAL_PORT, BAUD_RATE)
time.sleep(0.5)
init_angles = mc.get_angles()
init_mode = mc.get_transponder_mode()
log(f'  Initial angles: {init_angles}')
log(f'  Initial mode: {init_mode}')

log('')
log('Step 2: Switch to WiFi mode (1) via USB')
mc.set_transponder_mode(1)
time.sleep(1)
new_mode = mc.get_transponder_mode()
log(f'  Mode now: {new_mode}')

# Close USB completely
log('  Closing USB serial...')
if hasattr(mc, 'close'):
    mc.close()
del mc
time.sleep(1)
log('  USB closed.')

# Step 3: Send movement via raw WiFi
log('')
log('Step 3: Send [60,0,0,0,0,0] via WiFi raw socket')
cmd = encode_send_angles([60, 0, 0, 0, 0, 0], 40)
log(f'  Bytes: {cmd.hex()}')

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(5)
t_start = time.time()
s.connect((IP, PORT))
t_conn = time.time()
s.sendall(cmd)
t_send = time.time()
log(f'  Connected in {(t_conn - t_start)*1000:.0f}ms')
log(f'  Sent in {(t_send - t_conn)*1000:.0f}ms')

# Try to read any response
log('  Waiting for response...')
s.settimeout(2)
try:
    resp = s.recv(1024)
    log(f'  Response: {resp.hex() if resp else "empty"}')
except socket.timeout:
    log(f'  No response (timeout)')
except Exception as e:
    log(f'  Response error: {e}')
s.close()

# Step 4: Wait for movement
log('')
log('Step 4: Waiting 6 seconds for robot to move...')
time.sleep(6)

# Step 5: Switch back to UART and read
log('')
log('Step 5: Switch back to UART (0) via USB and read angles')
mc2 = MyCobot280(SERIAL_PORT, BAUD_RATE)
time.sleep(0.5)
mc2.set_transponder_mode(0)
time.sleep(1)

final_mode = mc2.get_transponder_mode()
final_angles = mc2.get_angles()
log(f'  Mode: {final_mode}')
log(f'  Final angles: {final_angles}')

# Check
log('')
log('=' * 40)
if final_angles and final_angles != -1 and abs(final_angles[0] - 60) < 10:
    log('PASS - Robot moved to ~60 degrees via WiFi!')
else:
    log('FAIL - Robot did NOT move')
    log(f'  Expected J1 ~60, got: {final_angles[0] if final_angles and final_angles != -1 else "N/A"}')

# Park
log('')
log('Parking...')
mc2.send_angles([0, 0, 0, 0, 0, 0], 40)
time.sleep(3)
park_angles = mc2.get_angles()
log(f'  Parked at: {park_angles}')
