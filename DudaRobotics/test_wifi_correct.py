#!/usr/bin/env python3
"""Test WiFi with CORRECT protocol codes.
Previous raw socket tests used wrong genre byte (0x20=GET_ANGLES instead of 0x22=SEND_ANGLES).
"""

import socket
import time
import datetime
from pymycobot import MyCobot280
from pymycobot.common import ProtocolCode
import struct

IP = '192.168.6.57'
PORT = 9000
SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 115200

def log(msg):
    ts = datetime.datetime.now().strftime('%H:%M:%S.%f')
    print(f'{ts} {msg}')

def encode_int16(values):
    """Encode list of ints as big-endian signed 16-bit, matching pymycobot."""
    result = []
    for v in values:
        result.extend(struct.pack(">h", v))
    return list(result)

def build_command(genre, data_bytes):
    """Build a complete protocol command."""
    length = len(data_bytes) + 2  # +2 for genre and footer
    cmd = [0xFE, 0xFE, length, genre] + data_bytes + [0xFA]
    return bytes(cmd)

def encode_send_angles(angles, speed):
    """Encode SEND_ANGLES command using correct protocol code 0x22."""
    int_angles = [int(a * 100) for a in angles]
    data = encode_int16(int_angles)
    data.append(speed)
    return build_command(ProtocolCode.SEND_ANGLES, data)

def wifi_send(cmd_bytes):
    """Send command over fresh WiFi connection with 1.5s init delay."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect((IP, PORT))
    time.sleep(1.5)  # Match pymycobot init delay
    s.sendall(cmd_bytes)
    time.sleep(0.1)
    s.close()

def read_angles_usb():
    mc = MyCobot280(SERIAL_PORT, BAUD_RATE)
    time.sleep(0.5)
    angles = mc.get_angles()
    if hasattr(mc, 'close'):
        mc.close()
    time.sleep(0.3)
    return angles

# Test 1: In UART mode (transponder_mode=0)
log('=== Test 1: CORRECT encoding, UART mode ===')
mc = MyCobot280(SERIAL_PORT, BAUD_RATE)
time.sleep(0.5)
mc.set_transponder_mode(0)
time.sleep(0.5)
init = mc.get_angles()
log(f'  Initial angles: {init}')
if hasattr(mc, 'close'):
    mc.close()
time.sleep(0.5)

cmd = encode_send_angles([45, 0, 0, 0, 0, 0], 40)
log(f'  Command bytes: {cmd.hex()}')
log(f'  Genre: 0x{cmd[3]:02X} (expected 0x22)')
wifi_send(cmd)
log(f'  Sent. Waiting 5s...')
time.sleep(5)
a1 = read_angles_usb()
ok1 = a1 and a1 != -1 and abs(a1[0] - 45) < 10
log(f'  Angles: {a1}')
log(f'  UART mode result: {"PASS" if ok1 else "FAIL"}')

# Park via USB
mc2 = MyCobot280(SERIAL_PORT, BAUD_RATE)
time.sleep(0.5)
mc2.send_angles([0,0,0,0,0,0], 40)
time.sleep(3)
if hasattr(mc2, 'close'):
    mc2.close()
time.sleep(0.5)

# Test 2: In WiFi mode (transponder_mode=1)
log('')
log('=== Test 2: CORRECT encoding, WiFi mode ===')
mc3 = MyCobot280(SERIAL_PORT, BAUD_RATE)
time.sleep(0.5)
mc3.set_transponder_mode(1)
time.sleep(1)
log(f'  Mode: {mc3.get_transponder_mode()}')
if hasattr(mc3, 'close'):
    mc3.close()
time.sleep(1)

cmd2 = encode_send_angles([45, 0, 0, 0, 0, 0], 40)
log(f'  Command bytes: {cmd2.hex()}')
wifi_send(cmd2)
log(f'  Sent. Waiting 5s...')
time.sleep(5)

# Switch back to UART to read
mc4 = MyCobot280(SERIAL_PORT, BAUD_RATE)
time.sleep(0.5)
mc4.set_transponder_mode(0)
time.sleep(0.5)
a2 = mc4.get_angles()
ok2 = a2 and a2 != -1 and abs(a2[0] - 45) < 10
log(f'  Angles: {a2}')
log(f'  WiFi mode result: {"PASS" if ok2 else "FAIL"}')

# Park
mc4.send_angles([0,0,0,0,0,0], 40)
time.sleep(3)

# Summary
log('')
log('=' * 40)
log(f'UART mode + correct WiFi cmd: {"PASS" if ok1 else "FAIL"}')
log(f'WiFi mode + correct WiFi cmd: {"PASS" if ok2 else "FAIL"}')
