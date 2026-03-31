#!/usr/bin/env python3
"""
MyCobot 280 WiFi communication helper.

Provides fast WiFi command sending via raw TCP sockets, bypassing
pymycobot's 1.5s initialization delay.

IMPORTANT: The M5Stack must be in WLAN Server mode for WiFi commands
to be processed. This typically requires selecting "Transponder" → 
"WiFi" from the M5Stack's physical touchscreen menu. Just calling
set_transponder_mode(1) via the API may not be sufficient.

Usage:
    from mycobot_wifi import MyCobotWiFi

    bot = MyCobotWiFi('192.168.6.57')
    bot.send_angles([45, 0, 0, 0, 0, 0], 40)
    bot.send_coords([150, 0, 200, -180, 0, -90], 40, mode=1)
    bot.close()
"""

import socket
import struct
import time
import threading

# Protocol constants (from pymycobot.common.ProtocolCode)
HEADER = 0xFE
FOOTER = 0xFA
SEND_ANGLE = 0x21
SEND_ANGLES = 0x22
SEND_COORD = 0x24
SEND_COORDS = 0x25
POWER_ON = 0x12
POWER_OFF = 0x13
RELEASE_ALL_SERVOS = 0x15
FOCUS_ALL_SERVOS = 0x17
SET_COLOR = 0x6A
STOP = 0x18
SET_FRESH_MODE = 0x47
IS_POWER_ON = 0x14


def _encode_int16(values):
    """Encode a list of integers as big-endian signed 16-bit bytes."""
    result = []
    for v in values:
        result.extend(struct.pack(">h", int(v)))
    return list(result)


def _build_command(genre, data_bytes=None):
    """Build a complete protocol frame: [0xFE, 0xFE, LEN, genre, data..., 0xFA]."""
    if data_bytes is None:
        data_bytes = []
    length = len(data_bytes) + 2  # genre + footer
    cmd = [HEADER, HEADER, length, genre] + data_bytes + [FOOTER]
    return bytes(cmd)


class MyCobotWiFi:
    """Fast WiFi communication with MyCobot 280 M5.
    
    Supports two connection strategies:
    - persistent: keep one TCP connection open (faster for rapid commands)
    - oneshot: new connection per command (more reliable if connection drops)
    """

    def __init__(self, ip, port=9000, connect_delay=1.5, strategy='persistent'):
        """
        Args:
            ip: Robot's WiFi IP address
            port: TCP port (default 9000)
            connect_delay: Seconds to wait after TCP connect before sending
            strategy: 'persistent' or 'oneshot'
        """
        self.ip = ip
        self.port = port
        self.connect_delay = connect_delay
        self.strategy = strategy
        self.sock = None
        self.lock = threading.Lock()
        
        if strategy == 'persistent':
            self._connect()

    def _connect(self):
        """Establish TCP connection to robot."""
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5)
        self.sock.connect((self.ip, self.port))
        if self.connect_delay > 0:
            time.sleep(self.connect_delay)

    def _send(self, cmd_bytes):
        """Send command bytes, using the configured strategy."""
        with self.lock:
            if self.strategy == 'oneshot':
                self._connect()
                try:
                    self.sock.sendall(cmd_bytes)
                finally:
                    self.sock.close()
                    self.sock = None
            else:
                try:
                    self.sock.sendall(cmd_bytes)
                except (BrokenPipeError, OSError):
                    # Reconnect and retry once
                    self._connect()
                    self.sock.sendall(cmd_bytes)

    def send_angles(self, angles, speed):
        """Send all 6 joint angles.
        
        Args:
            angles: list of 6 angle values in degrees
            speed: movement speed 1-100
        """
        int_angles = [int(a * 100) for a in angles]
        data = _encode_int16(int_angles)
        data.append(speed)
        self._send(_build_command(SEND_ANGLES, data))

    def send_coords(self, coords, speed, mode=1):
        """Send 6 coordinates [x, y, z, rx, ry, rz].
        
        Args:
            coords: [x, y, z, rx, ry, rz] - xyz in mm, rotations in degrees
            speed: movement speed 1-100
            mode: 0=angular, 1=linear
        """
        int_coords = []
        for i, c in enumerate(coords):
            if i < 3:
                int_coords.append(int(c * 10))    # xyz: multiply by 10
            else:
                int_coords.append(int(c * 100))   # rotation: multiply by 100
        data = _encode_int16(int_coords)
        data.append(speed)
        data.append(mode)
        self._send(_build_command(SEND_COORDS, data))

    def power_on(self):
        """Power on all servos."""
        self._send(_build_command(POWER_ON))

    def power_off(self):
        """Power off all servos."""
        self._send(_build_command(POWER_OFF))

    def release_all_servos(self):
        """Release all servos (free move)."""
        self._send(_build_command(RELEASE_ALL_SERVOS))

    def focus_all_servos(self):
        """Lock all servos."""
        self._send(_build_command(FOCUS_ALL_SERVOS))

    def stop(self):
        """Stop current movement."""
        self._send(_build_command(STOP))

    def set_color(self, r, g, b):
        """Set Atom LED color."""
        self._send(_build_command(SET_COLOR, [r, g, b]))

    def set_fresh_mode(self, mode):
        """Set fresh mode (0=interpolation, 1=refresh)."""
        self._send(_build_command(SET_FRESH_MODE, [mode]))

    def close(self):
        """Close TCP connection."""
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
