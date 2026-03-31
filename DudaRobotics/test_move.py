# test_move.py — verify the robot actually moves to commanded positions
#
# Uses USB serial for both read and write.
# WiFi and USB cannot be used simultaneously — the M5Stack only
# processes commands from one channel at a time.
#
# Usage:
#   python3 /ros2_ws/src/mycobot_ros2/DudaRobotics/test_move.py

import time
import datetime
from pymycobot import MyCobot280

SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 115200
TOLERANCE = 5.0  # degrees

def log(msg):
    print(f"{datetime.datetime.now()} {msg}")

def check_at_target(actual, target):
    if actual is None or actual == -1:
        return False
    return all(abs(a - t) < TOLERANCE for a, t in zip(actual, target))

# --- Open USB serial connection ---
log("Opening USB serial connection...")
mc = MyCobot280(SERIAL_PORT, BAUD_RATE)
time.sleep(0.5)

# === Test 1: Move to home ===
log("")
log("=== Test 1: Move to home [0,0,0,0,0,0] ===")
start = mc.get_angles()
log(f"  Before: {start}")

target1 = [0, 0, 0, 0, 0, 0]
log(f"  Sending: {target1}")
mc.send_angles(target1, 40)
time.sleep(5)

after1 = mc.get_angles()
log(f"  After:  {after1}")
log(f"  {'PASS' if check_at_target(after1, target1) else 'FAIL'}")

# === Test 2: Move joint 1 to 45° ===
log("")
log("=== Test 2: Move joint 1 to 45° ===")
target2 = [45, 0, 0, 0, 0, 0]
log(f"  Sending: {target2}")
mc.send_angles(target2, 40)
time.sleep(5)

after2 = mc.get_angles()
log(f"  After:  {after2}")
log(f"  {'PASS' if check_at_target(after2, target2) else 'FAIL'}")

# === Test 3: Move joint 1 to -45° ===
log("")
log("=== Test 3: Move joint 1 to -45° ===")
target3 = [-45, 0, 0, 0, 0, 0]
log(f"  Sending: {target3}")
mc.send_angles(target3, 40)
time.sleep(5)

after3 = mc.get_angles()
log(f"  After:  {after3}")
log(f"  {'PASS' if check_at_target(after3, target3) else 'FAIL'}")

# === Park ===
log("")
log("Parking to home...")
mc.send_angles([0, 0, 0, 0, 0, 0], 40)
time.sleep(4)

final = mc.get_angles()
log(f"  Final: {final}")

# === Summary ===
log("")
results = [
    ("Home [0,0,0,0,0,0]", check_at_target(after1, target1)),
    ("Joint1 → 45°",       check_at_target(after2, target2)),
    ("Joint1 → -45°",      check_at_target(after3, target3)),
    ("Park",               check_at_target(final, [0,0,0,0,0,0])),
]
log("=== Summary ===")
all_pass = True
for name, passed in results:
    status = "PASS" if passed else "FAIL"
    log(f"  {status}: {name}")
    if not passed:
        all_pass = False

log("")
if all_pass:
    log("ALL TESTS PASSED")
else:
    log("SOME TESTS FAILED")
