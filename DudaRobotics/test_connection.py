# test_connection.py — test myCobot 280 WiFi connectivity
#
# Findings:
#   - M5Stack WiFi server is WRITE-ONLY: it closes the socket after
#     receiving a command, so read commands (get_angles, is_power_on) return -1.
#   - One-connection-per-command is the only reliable pattern.
#   - send_angles/send_coords work fine with fresh connections.
#
# Usage:
#   python3 /ros2_ws/src/mycobot_ros2/DudaRobotics/test_connection.py

import time
import datetime
import socket
from pymycobot import MyCobot280Socket

MYCOBOT_IP = '192.168.6.57'
MYCOBOT_PORT = 9000

def log(msg):
    print(f"{datetime.datetime.now()} {msg}")

def send_angles(angles, speed=40):
    """One-shot: connect, send, close."""
    mc = MyCobot280Socket(MYCOBOT_IP, MYCOBOT_PORT)
    mc.send_angles(angles, speed)
    mc.sock.close()

def test_tcp_connect():
    """Test 1: Can we open a TCP connection at all?"""
    log("--- Test 1: TCP connect ---")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((MYCOBOT_IP, MYCOBOT_PORT))
        s.close()
        log("  PASS: TCP connection succeeded")
        return True
    except Exception as e:
        log(f"  FAIL: {e}")
        return False

def test_send_command():
    """Test 2: Can we send a command without error?"""
    log("--- Test 2: Send angles command ---")
    try:
        send_angles([0, 0, 0, 0, 0, 0])
        log("  PASS: send_angles completed without error")
        return True
    except Exception as e:
        log(f"  FAIL: {e}")
        return False

def test_move_visible():
    """Test 3: Does the robot physically move? Send distinct positions."""
    log("--- Test 3: Physical movement (watch the robot!) ---")
    errors = 0

    log("  Sending [0,0,0,0,0,0] (home)...")
    try:
        send_angles([0, 0, 0, 0, 0, 0])
    except Exception as e:
        log(f"  FAIL at home: {e}")
        errors += 1
    time.sleep(4)

    log("  Sending [45,0,0,0,0,0] (joint 1 → 45°)...")
    try:
        send_angles([45, 0, 0, 0, 0, 0])
    except Exception as e:
        log(f"  FAIL at 45°: {e}")
        errors += 1
    time.sleep(4)

    log("  Sending [-45,0,0,0,0,0] (joint 1 → -45°)...")
    try:
        send_angles([-45, 0, 0, 0, 0, 0])
    except Exception as e:
        log(f"  FAIL at -45°: {e}")
        errors += 1
    time.sleep(4)

    log("  Sending [0,0,0,0,0,0] (back to home)...")
    try:
        send_angles([0, 0, 0, 0, 0, 0])
    except Exception as e:
        log(f"  FAIL at home: {e}")
        errors += 1
    time.sleep(3)

    if errors == 0:
        log("  PASS: All 4 movement commands sent OK")
        log("  >>> Visually confirm: did the base rotate right, then left, then center?")
        return True
    else:
        log(f"  FAIL: {errors} command(s) errored")
        return False

# === Main loop: retry until all tests pass ===
MAX_ATTEMPTS = 5
for attempt in range(1, MAX_ATTEMPTS + 1):
    log(f"")
    log(f"========== Attempt {attempt}/{MAX_ATTEMPTS} ==========")

    if not test_tcp_connect():
        log(f"TCP failed. Retrying in 5s...")
        time.sleep(5)
        continue

    if not test_send_command():
        log(f"Send failed. Retrying in 5s...")
        time.sleep(5)
        continue

    if not test_move_visible():
        log(f"Movement failed. Retrying in 5s...")
        time.sleep(5)
        continue

    log("")
    log("========== ALL TESTS PASSED ==========")
    log("Note: read commands (get_angles, get_coords) do NOT work over WiFi.")
    log("      The M5Stack WiFi server is write-only (closes socket before reply).")
    log("      Use USB serial for reading robot state.")
    break
else:
    log("")
    log(f"========== FAILED after {MAX_ATTEMPTS} attempts ==========")
