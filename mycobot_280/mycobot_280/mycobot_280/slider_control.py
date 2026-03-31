import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import time
import math
import socket
import struct
import pymycobot
from packaging import version

# min low version require
MIN_REQUIRE_VERSION = '3.6.1'

current_verison = pymycobot.__version__
print('current pymycobot library version: {}'.format(current_verison))
if version.parse(current_verison) < version.parse(MIN_REQUIRE_VERSION):
    raise RuntimeError('The version of pymycobot library must be greater than {} or higher. The current version is {}. Please upgrade the library version.'.format(
        MIN_REQUIRE_VERSION, current_verison))
else:
    print('pymycobot library version meets the requirements!')
    from pymycobot import MyCobot280


class MyCobot280WiFi:
    def __init__(self, ip, tcp_port, connect_delay=1.5):
        self.ip = ip
        self.tcp_port = tcp_port
        self.connect_delay = connect_delay
        self.sock = None
        self._connect()

    def _connect(self):
        if self.sock is not None:
            try:
                self.sock.close()
            except OSError:
                pass
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5)
        self.sock.connect((self.ip, self.tcp_port))
        time.sleep(self.connect_delay)

    def _build_send_angles_command(self, angles, speed):
        payload = []
        for angle in angles:
            payload.extend(struct.pack('>h', int(angle * 100)))
        payload.append(speed)
        length = len(payload) + 2
        return bytes([0xFE, 0xFE, length, 0x22] + payload + [0xFA])

    def send_angles(self, angles, speed):
        command = self._build_send_angles_command(angles, speed)
        try:
            self.sock.sendall(command)
        except OSError:
            self._connect()
            self.sock.sendall(command)

    def close(self):
        if self.sock is not None:
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None


class Slider_Subscriber(Node):
    def __init__(self):
        super().__init__("control_slider")
        self.subscription = self.create_subscription(
            JointState,
            "joint_states",
            self.listener_callback,
            10
        )
        self.subscription

        # self.robot_m5 = os.popen("ls /dev/ttyUSB*").readline()[:-1]
        # self.robot_wio = os.popen("ls /dev/ttyACM*").readline()[:-1]
        # if self.robot_m5:
        #     port = self.robot_m5
        # else:
        #     port = self.robot_wio
        self.declare_parameter('connection_type', 'serial')
        self.declare_parameter('port', '/dev/ttyUSB0')
        self.declare_parameter('baud', 115200)
        self.declare_parameter('ip', '192.168.6.57')
        self.declare_parameter('tcp_port', 9000)
        connection_type = self.get_parameter('connection_type').get_parameter_value().string_value
        port = self.get_parameter('port').get_parameter_value().string_value
        baud = self.get_parameter('baud').get_parameter_value().integer_value
        ip = self.get_parameter('ip').get_parameter_value().string_value
        tcp_port = self.get_parameter('tcp_port').get_parameter_value().integer_value

        self.get_logger().info(
            "connection_type:%s, port:%s, baud:%d, ip:%s, tcp_port:%d"
            % (connection_type, port, baud, ip, tcp_port)
        )

        if connection_type == 'wifi':
            self.mc = MyCobot280WiFi(ip, tcp_port)
        else:
            self.mc = MyCobot280(port, baud)
            time.sleep(0.05)
            self.mc.set_fresh_mode(1)
            time.sleep(0.05)

    def listener_callback(self, msg):

        data_list = []
        for _, value in enumerate(msg.position):
            radians_to_angles = round(math.degrees(value), 2)
            data_list.append(radians_to_angles)

        print('data_list: {}'.format(data_list))
        self.mc.send_angles(data_list, 25)


def main(args=None):
    rclpy.init(args=args)
    slider_subscriber = Slider_Subscriber()

    rclpy.spin(slider_subscriber)

    slider_subscriber.mc.close()
    slider_subscriber.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
