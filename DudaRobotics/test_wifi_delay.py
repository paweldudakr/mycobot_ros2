#!/usr/bin/env python3
"""Test WiFi with 1.5s delay after connect (like pymycobot does)."""

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

# Step 1: Ensure WiFi mode
log('Setting WiFi mode via USB...')
mc = MyCobot280(SERIAL_PORT, BAUD_RATE)
time.sleep(0.5)
mc.set_transponder_mode(1)
time.sleep(1)
mode = mc.get_transponder_mode()
log(f'  Mode: {mode}')
if hasattr(mc, 'close'):
    mc.close()
del mc
time.sleep(1)

# Step 2: Connect WiFi with delays
delays = [0, 0.5, 1.0, 1.5, 2.0]
for delay in delays:
    log(f'--- Testing with {delay}s delay after connect ---')
    
    # Ensure WiFi mode
    mc_tmp = MyCobot280(SERIAL_PORT, BAUD_RATE)
    time.sleep(0.5)
    mc_tmp.set_transponder_mode(1)
    time.sleep(0.5)
    if hasattr(mc_tmp, 'close'):
        mc_tmp.close()
    del mc_tmp
    time.sleep(0.5)
    
    target = 45 if delay in [0, 1.0, 2.0] else -45
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect((IP, PORT))
    
    if delay > 0:
        time.sleep(delay)
    
    cmd = encode_send_angles([target, 0, 0, 0, 0, 0], 40)
    try:
        s.sendall(cmd)
        log(f'  Sent [{target},0,0,0,0,0]')
    except Exception as e:
        log(f'  Send failed: {e}')
        s.close()
        continue
    
    # Check response
    s.settimeout(1)
    try:
        resp = s.recv(1024)
        status = resp.hex() if resp else 'empty'
        log(f'  Response: {status}')
    except socket.timeout:
        log(f'  No response (timeout 1s)')
    except Exception as e:
        log(f'  Recv error: {e}')
    
    s.close()
    time.sleep(5)
    
    # Verify via USB
    mc_v = MyCobot280(SERIAL_PORT, BAUD_RATE)
    time.sleep(0.5)
    mc_v.set_transponder_mode(0)
    time.sleep(0.5)
    angles = mc_v.get_angles()
    ok = angles and angles != -1 and abs(angles[0] - target) < 10
    result = 'PASS' if ok else 'FAIL'
    log(f'  Angles: {angles}')
    log(f'  {result} (expected J1={target})')
    
    # Park
    mc_v.send_angles([0, 0, 0, 0, 0, 0], 40)
    time.sleep(3)
    if hasattr(mc_v, 'close'):
        mc_v.close()
    del mc_v
    time.sleep(0.5)

log('Done.')
