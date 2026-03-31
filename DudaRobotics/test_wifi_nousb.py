#!/usr/bin/env python3
"""
Pure WiFi test — NO USB serial required.
Run this AFTER disconnecting the USB cable.

Tests:
  1. TCP connectivity
  2. Send movement command via WiFi (visual confirmation only)
  3. Send LED color change (very visible feedback)
  4. Send multiple movements in sequence
"""

import socket
import struct
import time
import datetime

IP = '192.168.6.57'
PORT = 9000

# Protocol codes (verified from pymycobot source)
HEADER = 0xFE
FOOTER = 0xFA
SEND_ANGLES = 0x22
SEND_COORDS = 0x25
SET_COLOR = 0x6A
POWER_ON = 0x12
IS_POWER_ON = 0x14

def log(msg=''):
    ts = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]
    print(f'{ts} {msg}')

def encode_int16(values):
    result = []
    for v in values:
        result.extend(struct.pack(">h", int(v)))
    return list(result)

def build_cmd(genre, data=None):
    if data is None:
        data = []
    length = len(data) + 2
    return bytes([HEADER, HEADER, length, genre] + data + [FOOTER])

def send_cmd(cmd_bytes, label="", wait_after=0, keep_open=False):
    """Send a single command. Returns socket if keep_open=True."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    try:
        s.connect((IP, PORT))
    except Exception as e:
        log(f'  CONNECT FAILED: {e}')
        return None

    if keep_open:
        time.sleep(1.5)  # pymycobot init delay

    try:
        s.sendall(cmd_bytes)
        if label:
            log(f'  Sent: {label} [{cmd_bytes.hex()}]')
    except Exception as e:
        log(f'  SEND FAILED: {e}')
        s.close()
        return None

    # Try to read any response
    s.settimeout(1)
    try:
        resp = s.recv(1024)
        if resp:
            log(f'  Response: {resp.hex()} ({len(resp)} bytes)')
        else:
            log(f'  Server closed write-side (empty response)')
    except socket.timeout:
        log(f'  No response (timeout 1s) - connection still open')
    except ConnectionResetError:
        log(f'  Connection reset by server')
    except OSError as e:
        log(f'  Recv error: {e}')

    if not keep_open:
        s.close()
        if wait_after > 0:
            time.sleep(wait_after)
        return None
    return s

def send_angles(angles, speed, **kwargs):
    int_angles = [int(a * 100) for a in angles]
    data = encode_int16(int_angles)
    data.append(speed)
    label = f'send_angles({angles}, {speed})'
    return send_cmd(build_cmd(SEND_ANGLES, data), label, **kwargs)

def set_color(r, g, b, **kwargs):
    label = f'set_color({r},{g},{b})'
    return send_cmd(build_cmd(SET_COLOR, [r, g, b]), label, **kwargs)

# ====================================================
log('=' * 55)
log('MyCobot 280 WiFi-Only Test (no USB)')
log('=' * 55)
log()

# Test 1: TCP connectivity
log('--- Test 1: TCP Connectivity ---')
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    t0 = time.time()
    s.connect((IP, PORT))
    dt = (time.time() - t0) * 1000
    log(f'  Connected to {IP}:{PORT} in {dt:.0f}ms')

    # Check initial server behavior
    s.settimeout(2)
    try:
        data = s.recv(1024)
        log(f'  Server sent: {data.hex() if data else "(empty/closed)"}')
    except socket.timeout:
        log(f'  Server silent (no greeting, connection stays open)')
    s.close()
    log(f'  PASS')
except Exception as e:
    log(f'  FAILED: {e}')
    log(f'  Cannot reach robot. Check: WiFi connection, IP address, firewall.')
    exit(1)

# Test 2: LED color change (most visible instant feedback)
log()
log('--- Test 2: LED Color Change ---')
log('  Watch the Atom LED on the robot head!')
log()

time.sleep(1)
log('  Setting RED...')
set_color(255, 0, 0, wait_after=2)

log('  Setting GREEN...')
set_color(0, 255, 0, wait_after=2)

log('  Setting BLUE...')
set_color(0, 0, 255, wait_after=2)

log('  Setting WHITE...')
set_color(255, 255, 255, wait_after=1)

log()
log('  >> Did the LED change colors? (RED → GREEN → BLUE → WHITE)')
log('  >> If YES: WiFi commands are working!')
log('  >> If NO:  M5Stack is not processing WiFi commands.')
log()

# Test 3: Movement (slow, safe, visible)
log('--- Test 3: Movement ---')
log('  !! WARNING: Robot will try to move !!')
log('  Sending joint 1 to 30 degrees...')
send_angles([30, 0, 0, 0, 0, 0], 20, wait_after=5)

log('  Sending joint 1 to -30 degrees...')
send_angles([-30, 0, 0, 0, 0, 0], 20, wait_after=5)

log('  Parking (home position)...')
send_angles([0, 0, 0, 0, 0, 0], 20, wait_after=4)

log()
log('  >> Did the robot move? (30° → -30° → home)')
log()

# Test 4: Persistent connection (send multiple on same socket)
log('--- Test 4: Persistent Connection ---')
log('  Opening persistent connection with 1.5s init delay...')
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(5)
s.connect((IP, PORT))
time.sleep(1.5)

cmds = [
    (build_cmd(SET_COLOR, [255, 0, 0]), 'LED RED'),
    (build_cmd(SET_COLOR, [0, 255, 0]), 'LED GREEN'),
    (build_cmd(SET_COLOR, [0, 0, 255]), 'LED BLUE'),
]

for cmd_bytes, label in cmds:
    try:
        s.sendall(cmd_bytes)
        log(f'  Sent: {label}')
        time.sleep(1)
    except Exception as e:
        log(f'  Failed: {label} - {e}')
        break

s.close()

log()
log('=' * 55)
log('TEST COMPLETE')
log('=' * 55)
log()
log('If LED changed colors and robot moved:')
log('  WiFi is WORKING! You can use stir.py --wifi')
log()
log('If nothing happened:')
log('  The M5Stack needs to be in WLAN Server mode.')
log('  On the M5Stack screen: Transponder → WiFi')
log('  Then re-run this test.')
