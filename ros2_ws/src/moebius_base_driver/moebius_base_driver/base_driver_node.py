#!/usr/bin/env python3
import math
import threading
import time
from typing import Optional

import rclpy
from geometry_msgs.msg import Quaternion, TransformStamped, Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import JointState
from tf2_ros import TransformBroadcaster

try:
    import serial
except ImportError:  # pragma: no cover
    serial = None


class MoebiusBaseDriver(Node):
    """Serial bridge for a differential-drive Moebius robot.

    TX protocol: CMD,<linear_mps>,<angular_rps>\n
    RX protocol: FB,<left_ticks>,<right_ticks>,<gyro_z>,<battery_v>\n
    The protocol is intentionally simple so the existing firmware can be
    adapted incrementally. Add CRC in firmware before field deployment.
    """

    def __init__(self) -> None:
        super().__init__('moebius_base_driver')

        self.declare_parameter('port', '/dev/ttyACM0')
        self.declare_parameter('baudrate', 115200)
        self.declare_parameter('wheel_radius', 0.08)
        self.declare_parameter('wheel_separation', 0.36)
        self.declare_parameter('ticks_per_revolution', 2048.0)
        self.declare_parameter('publish_tf', True)
        self.declare_parameter('command_timeout', 0.5)
        self.declare_parameter('serial_timeout', 0.05)

        self.port = str(self.get_parameter('port').value)
        self.baudrate = int(self.get_parameter('baudrate').value)
        self.wheel_radius = float(self.get_parameter('wheel_radius').value)
        self.wheel_separation = float(self.get_parameter('wheel_separation').value)
        self.ticks_per_revolution = float(self.get_parameter('ticks_per_revolution').value)
        self.publish_tf = bool(self.get_parameter('publish_tf').value)
        self.command_timeout = float(self.get_parameter('command_timeout').value)
        self.serial_timeout = float(self.get_parameter('serial_timeout').value)

        self.odom_pub = self.create_publisher(Odometry, 'odom', 20)
        self.joint_pub = self.create_publisher(JointState, 'joint_states', 20)
        self.create_subscription(Twist, 'cmd_vel', self.cmd_vel_callback, 20)
        self.tf_broadcaster = TransformBroadcaster(self)

        self._lock = threading.Lock()
        self._serial: Optional[object] = None
        self._last_cmd_time = self.get_clock().now()
        self._last_left_ticks: Optional[int] = None
        self._last_right_ticks: Optional[int] = None
        self._last_feedback_time = self.get_clock().now()
        self._x = 0.0
        self._y = 0.0
        self._yaw = 0.0

        self._connect_serial()
        self.create_timer(0.02, self.poll_serial)
        self.create_timer(0.05, self.watchdog)

    def _connect_serial(self) -> None:
        if serial is None:
            self.get_logger().error('pyserial is not installed. Run rosdep or pip install pyserial.')
            return
        try:
            self._serial = serial.Serial(
                self.port,
                self.baudrate,
                timeout=self.serial_timeout,
                write_timeout=self.serial_timeout,
            )
            self.get_logger().info(f'Connected to {self.port} at {self.baudrate} baud')
        except serial.SerialException as exc:
            self.get_logger().error(f'Cannot open serial port {self.port}: {exc}')
            self._serial = None

    def _write_line(self, line: str) -> None:
        with self._lock:
            if self._serial is None:
                return
            try:
                self._serial.write(line.encode('ascii'))
            except (serial.SerialException, serial.SerialTimeoutException) as exc:
                self.get_logger().error(f'Serial write failed: {exc}')
                self._serial = None

    def cmd_vel_callback(self, msg: Twist) -> None:
        self._last_cmd_time = self.get_clock().now()
        self._write_line(f'CMD,{msg.linear.x:.4f},{msg.angular.z:.4f}\n')

    def watchdog(self) -> None:
        age = (self.get_clock().now() - self._last_cmd_time).nanoseconds * 1e-9
        if age > self.command_timeout:
            self._write_line('CMD,0.0000,0.0000\n')

    def poll_serial(self) -> None:
        if self._serial is None:
            return
        try:
            raw = self._serial.readline()
        except serial.SerialException as exc:
            self.get_logger().error(f'Serial read failed: {exc}')
            self._serial = None
            return
        if not raw:
            return
        try:
            line = raw.decode('ascii').strip()
            fields = line.split(',')
            if len(fields) < 3 or fields[0] != 'FB':
                self.get_logger().warning(f'Ignoring malformed feedback: {line}')
                return
            left_ticks = int(fields[1])
            right_ticks = int(fields[2])
            self.update_odometry(left_ticks, right_ticks)
        except (UnicodeDecodeError, ValueError) as exc:
            self.get_logger().warning(f'Unable to parse feedback: {exc}')

    def update_odometry(self, left_ticks: int, right_ticks: int) -> None:
        now = self.get_clock().now()
        if self._last_left_ticks is None or self._last_right_ticks is None:
            self._last_left_ticks = left_ticks
            self._last_right_ticks = right_ticks
            self._last_feedback_time = now
            return

        dt = max((now - self._last_feedback_time).nanoseconds * 1e-9, 1e-6)
        dlt = left_ticks - self._last_left_ticks
        drt = right_ticks - self._last_right_ticks
        meters_per_tick = 2.0 * math.pi * self.wheel_radius / self.ticks_per_revolution
        dl = dlt * meters_per_tick
        dr = drt * meters_per_tick
        ds = 0.5 * (dr + dl)
        dtheta = (dr - dl) / self.wheel_separation

        heading_mid = self._yaw + 0.5 * dtheta
        self._x += ds * math.cos(heading_mid)
        self._y += ds * math.sin(heading_mid)
        self._yaw = math.atan2(math.sin(self._yaw + dtheta), math.cos(self._yaw + dtheta))

        linear = ds / dt
        angular = dtheta / dt
        q = Quaternion()
        q.z = math.sin(self._yaw * 0.5)
        q.w = math.cos(self._yaw * 0.5)

        stamp = now.to_msg()
        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_footprint'
        odom.pose.pose.position.x = self._x
        odom.pose.pose.position.y = self._y
        odom.pose.pose.orientation = q
        odom.twist.twist.linear.x = linear
        odom.twist.twist.angular.z = angular
        self.odom_pub.publish(odom)

        left_pos = left_ticks * 2.0 * math.pi / self.ticks_per_revolution
        right_pos = right_ticks * 2.0 * math.pi / self.ticks_per_revolution
        joints = JointState()
        joints.header.stamp = stamp
        joints.name = ['left_wheel_joint', 'right_wheel_joint']
        joints.position = [left_pos, right_pos]
        joints.velocity = [dl / self.wheel_radius / dt, dr / self.wheel_radius / dt]
        self.joint_pub.publish(joints)

        if self.publish_tf:
            transform = TransformStamped()
            transform.header.stamp = stamp
            transform.header.frame_id = 'odom'
            transform.child_frame_id = 'base_footprint'
            transform.transform.translation.x = self._x
            transform.transform.translation.y = self._y
            transform.transform.rotation = q
            self.tf_broadcaster.sendTransform(transform)

        self._last_left_ticks = left_ticks
        self._last_right_ticks = right_ticks
        self._last_feedback_time = now

    def destroy_node(self) -> bool:
        self._write_line('CMD,0.0000,0.0000\n')
        time.sleep(0.02)
        if self._serial is not None:
            self._serial.close()
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = MoebiusBaseDriver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
