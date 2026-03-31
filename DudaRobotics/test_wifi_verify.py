#!/usr/bin/env python3
"""
WiFi verification test for MyCobot 280 M5.

Before running this test, the M5Stack must be in WLAN Server mode.
To set this up on the M5Stack screen:
  1. Power on the robot
  2. On the M5Stack display, tap "Transponder"
  3. Select "WiFi" or "WLAN Server"
  4. Wait for it to show the IP address
  5. Run this script

This script has 3 phases:
  Phase A: Check WiFi connectivity (always works)
  Phase B: Send movement command via WiFi, verify via USB
  Phase C: Send movement command via pymycobot WiFi class
"""

import socket
import time
import datetime
import sys

def log(msg=''):
    ts = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]
    print(f'{ts} {msg}')

# Configuration
IP = '192.168.6.57'
PORT = 9000
SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 115200
TOLERANCE = 10.0

results = []

# ============================================================
# Phase A: WiFi connectivity
# ============================================================
log('=' * 50)
log('Phase A: WiFi Connectivity')
log('=' * 50)

# A1: TCP connect
log('A1: TCP connect test...')
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    t0 = time.time()
    s.connect((IP, PORT))
    dt = (time.time() - t0) * 1000
    log(f'    Connected in {dt:.0f}ms')
    results.append(('A1 TCP connect', True))
    
    # Check if server sends anything
    s.settimeout(1)
    try:
        data = s.recv(1024)
        if data:
            log(f'    Server greeting: {data.hex()}')
        else:
            log(f'    Server closed write-side immediately (half-open socket)')
    except socket.timeout:
        log(f'    No greeting (timeout) - connection stays open')
    s.close()
except Exception as e:
    log(f'    FAILED: {e}')
    results.append(('A1 TCP connect', False))

# ============================================================
# Phase B: Raw socket movement test
# ============================================================
log()
log('=' * 50)
log('Phase B: Raw socket command → USB verify')
log('=' * 50)

try:
    import struct
    from pymycobot import MyCobot280

    def encode_send_angles(angles, speed):
        genre = 0x22  # SEND_ANGLES
        int_angles = [int(a * 100) for a in angles]
        data = []
        for v in int_angles:
            data.extend(struct.pack(">h", v))
        data = list(data)
        data.append(speed)
        length = len(data) + 2
        return bytes([0xFE, 0xFE, length, genre] + data + [0xFA])

    # Read initial position via USB
    log('B0: Reading initial position via USB...')
    mc = MyCobot280(SERIAL_PORT, BAUD_RATE)
    time.sleep(0.5)
    init = mc.get_angles()
    mode = mc.get_transponder_mode()
    log(f'    Initial angles: {init}')
    log(f'    Transponder mode: {mode} (0=UART, 1=WiFi, 2=BT)')
    if hasattr(mc, 'close'):
        mc.close()
    time.sleep(0.5)

    # Send via WiFi
    target = 45.0
    log(f'B1: Sending [{target},0,0,0,0,0] via raw WiFi socket...')
    cmd = encode_send_angles([target, 0, 0, 0, 0, 0], 40)
    log(f'    Bytes: {cmd.hex()}')
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect((IP, PORT))
    time.sleep(1.5)  # pymycobot-compatible delay
    s.sendall(cmd)
    s.close()
    log(f'    Sent. Waiting 5s for movement...')
    time.sleep(5)

    # Read via USB
    mc2 = MyCobot280(SERIAL_PORT, BAUD_RATE)
    time.sleep(0.5)
    after = mc2.get_angles()
    log(f'    Angles after: {after}')
    
    moved = after and after != -1 and abs(after[0] - target) < TOLERANCE
    log(f'    B1 result: {"PASS - ROBOT MOVED!" if moved else "FAIL - no movement"}')
    results.append(('B1 raw WiFi send', moved))

    # Park
    mc2.send_angles([0, 0, 0, 0, 0, 0], 40)
    time.sleep(3)
    if hasattr(mc2, 'close'):
        mc2.close()
    time.sleep(0.5)
    
except Exception as e:
    log(f'    Phase B error: {e}')
    results.append(('B1 raw WiFi send', False))

# ============================================================
# Phase C: pymycobot WiFi class test
# ============================================================
log()
log('=' * 50)
log('Phase C: MyCobot280Socket test')
log('=' * 50)

try:
    from pymycobot import MyCobot280Socket

    log('C1: Creating MyCobot280Socket...')
    mc_wifi = MyCobot280Socket(IP, PORT)
    log('    Connected.')

    target2 = -45.0
    log(f'C2: send_angles([{target2},0,0,0,0,0], 40)...')
    ret = mc_wifi.send_angles([target2, 0, 0, 0, 0, 0], 40)
    log(f'    Returned: {ret}')
    
    log('C3: Trying get_angles via WiFi...')
    wifi_angles = mc_wifi.get_angles()
    log(f'    WiFi get_angles: {wifi_angles}')
    
    mc_wifi.close()
    
    log('    Waiting 5s...')
    time.sleep(5)

    # Verify via USB
    mc3 = MyCobot280(SERIAL_PORT, BAUD_RATE)
    time.sleep(0.5)
    after2 = mc3.get_angles()
    log(f'    Angles via USB: {after2}')
    
    moved2 = after2 and after2 != -1 and abs(after2[0] - target2) < TOLERANCE
    log(f'    C2 result: {"PASS" if moved2 else "FAIL"}')
    results.append(('C2 pymycobot WiFi', moved2))
    
    wifi_read_ok = wifi_angles and wifi_angles != -1
    log(f'    C3 WiFi read: {"PASS" if wifi_read_ok else "FAIL (expected - WiFi is write-only)"}')
    results.append(('C3 WiFi read', wifi_read_ok))

    # Park
    mc3.send_angles([0, 0, 0, 0, 0, 0], 40)
    time.sleep(3)
    if hasattr(mc3, 'close'):
        mc3.close()

except Exception as e:
    log(f'    Phase C error: {e}')
    results.append(('C2 pymycobot WiFi', False))
    results.append(('C3 WiFi read', False))

# ============================================================
# Summary
# ============================================================
log()
log('=' * 50)
log('SUMMARY')
log('=' * 50)
any_fail = False
for name, ok in results:
    status = 'PASS' if ok else 'FAIL'
    log(f'  {name:25s} {status}')
    if not ok:
        any_fail = True

log()
if not any_fail:
    log('ALL TESTS PASSED - WiFi is fully working!')
elif results[0][1] and not any(ok for name, ok in results if 'send' in name.lower()):
    log('WiFi CONNECTS but commands are NOT EXECUTED.')
    log('')
    log('This likely means the M5Stack is NOT in WLAN Server mode.')
    log('To fix this, please:')
    log('  1. Look at the M5Stack screen on the robot')
    log('  2. Navigate to: Transponder → WiFi/WLAN Server')
    log('  3. Wait for it to display the IP address')
    log('  4. Re-run this test')
else:
    log('Some tests failed.')
