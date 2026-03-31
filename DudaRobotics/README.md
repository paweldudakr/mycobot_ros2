# DudaRobotics — MyCobot 280 M5 Control Scripts

Scripts for controlling the MyCobot 280 M5 robot arm, supporting both USB serial and WiFi connections.

## Requirements

- Docker container `mycobot` running ROS2 Humble (see root `docker-compose.yml`)
- `pymycobot` v4.0.4+ installed in the container
- MyCobot 280 M5 Stack robot

## Enabling WiFi Connection

The MyCobot 280 M5 supports WiFi (TCP socket) communication, but it requires proper setup. **USB and WiFi cannot be active at the same time** — the M5Stack only processes commands from one channel.

### Step 1: Configure WiFi Credentials (one-time, via USB)

Connect the robot via USB and run:

```bash
docker compose exec mycobot python3 /ros2_ws/src/mycobot_ros2/DudaRobotics/wifi_config.py
```

This reads the current WiFi SSID and password. To change them, edit `NEW_SSID` and `NEW_PASSWORD` in `wifi_config.py`, then run:

```bash
docker compose exec mycobot python3 /ros2_ws/src/mycobot_ros2/DudaRobotics/wifi_config.py --set
```

### Step 2: Disconnect USB Cable

**This is critical.** The M5Stack ignores WiFi commands while USB is physically connected. Unplug the USB cable from the robot.

### Step 3: Restart the Robot

Power-cycle the robot (turn off and on). After restarting, the M5Stack will boot into WiFi/WLAN Server mode and begin listening for TCP connections on port 9000.

### Step 4: Verify WiFi Connection

Run the WiFi test (no USB needed):

```bash
docker compose exec mycobot python3 /ros2_ws/src/mycobot_ros2/DudaRobotics/test_wifi_nousb.py
```

This will:
1. Test TCP connectivity to the robot
2. Change the Atom LED color (RED → GREEN → BLUE → WHITE)
3. Move joint 1 (30° → -30° → home)

If the LED changes colors and the robot moves, WiFi is working.

### Step 5: Run Scripts in WiFi Mode

```bash
docker compose exec mycobot python3 /ros2_ws/src/mycobot_ros2/DudaRobotics/stir.py --wifi
```

Optional arguments:
- `--ip 192.168.6.57` — Robot IP address (default: `192.168.6.57`)
- `--port 9000` — TCP port (default: `9000`)

### Switching Back to USB

1. Power off the robot
2. Reconnect the USB cable
3. Power on the robot
4. Run scripts without the `--wifi` flag:

```bash
docker compose exec mycobot python3 /ros2_ws/src/mycobot_ros2/DudaRobotics/stir.py
```

## WiFi Limitations

| Feature | USB Serial | WiFi |
|---|---|---|
| Send commands (angles, coords) | Yes | Yes |
| Read state (get_angles, get_coords) | Yes | **No** (returns -1) |
| Simultaneous use | — | **No** (only one channel at a time) |
| Requires USB cable | Yes | No |

WiFi is **write-only**: you can send movement commands but cannot read the robot's current position. Use USB serial when you need position feedback.

## Scripts

| Script | Description |
|---|---|
| `stir.py` | Stirring motion — moves arm in circles inside a glass. Supports `--wifi` flag. |
| `wifi_config.py` | Read/set WiFi credentials via USB serial. Use `--set` to change. |
| `mycobot_wifi.py` | WiFi helper module — fast raw TCP socket communication, used by `stir.py --wifi`. |
| `teach.py` | Record and replay trajectories. |
| `test_wifi_nousb.py` | WiFi verification test (no USB required). |
| `test_move.py` | Movement verification with angle readback (USB only). |
| `test_connection.py` | Connection diagnostics. |

## Network Details

| Setting | Value |
|---|---|
| Default IP | `192.168.6.57` |
| TCP Port | `9000` |
| WiFi SSID | `MyCobotWiFi2.4G` |
| WiFi Password | `mycobot123` |
| Protocol | Binary: `[0xFE, 0xFE, LEN, CMD, DATA..., 0xFA]` |
