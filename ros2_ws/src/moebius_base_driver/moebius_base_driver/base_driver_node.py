#!/usr/bin/env python3
import math
import threading
import time
from typing import Optional

import rclpy
from geometry_msgs.msg import Quaternion, TransformStamped, Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import BatteryState, Imu, JointState
from std_msgs.msg import Bool
from tf2_ros import TransformBroadcaster

try:
    import serial
except ImportError:  # pragma: no cover
    serial = None


class MoebiusBaseDriver(Node):
    """ROS 2 Jazzy serial bridge for the STM32F103RCT6 controller.

    TX: CMD,<linear_mps>,<angular_rps>\n
    RX legacy: FB,<left_ticks>,<right_ticks>,<gyro_z>,<battery_v>\n
    RX extended: FB,left,right,gz,battery,estop,stamp,ax,ay,az,gx,gy,imu_valid\n
    """

    def __init__(self) -> None:
        super().__init__('moebius_base_driver')
        self.declare_parameter('port', '/dev/ttyUSB0')
        self.declare_parameter('baudrate', 115200)
        self.declare_parameter('wheel_radius', 0.04)
        self.declare_parameter('wheel_separation', 0.26)
        self.declare_parameter('ticks_per_revolution', 1300.0)
        self.declare_parameter('publish_tf', True)
        self.declare_parameter('command_timeout', 0.3)
        self.declare_parameter('serial_timeout', 0.05)
        self.declare_parameter('imu_frame', 'imu_link')

        self.port = str(self.get_parameter('port').value)
        self.baudrate = int(self.get_parameter('baudrate').value)
        self.wheel_radius = float(self.get_parameter('wheel_radius').value)
        self.wheel_separation = float(self.get_parameter('wheel_separation').value)
        self.ticks_per_revolution = float(self.get_parameter('ticks_per_revolution').value)
        self.publish_tf = bool(self.get_parameter('publish_tf').value)
        self.command_timeout = float(self.get_parameter('command_timeout').value)
        self.serial_timeout = float(self.get_parameter('serial_timeout').value)
        self.imu_frame = str(self.get_parameter('imu_frame').value)

        self.odom_pub = self.create_publisher(Odometry, 'odom', 20)
        self.joint_pub = self.create_publisher(JointState, 'joint_states', 20)
        self.imu_pub = self.create_publisher(Imu, 'imu/data_raw', 20)
        self.battery_pub = self.create_publisher(BatteryState, 'battery_state', 10)
        self.estop_pub = self.create_publisher(Bool, 'emergency_stop', 10)
        self.create_subscription(Twist, 'cmd_vel', self.cmd_vel_callback, 20)
        self.tf_broadcaster = TransformBroadcaster(self)

        self._lock = threading.Lock()
        self._serial: Optional[object] = None
        self._last_cmd_time = self.get_clock().now()
        self._last_left_ticks: Optional[int] = None
        self._last_right_ticks: Optional[int] = None
        self._last_feedback_time = self.get_clock().now()
        self._x = self._y = self._yaw = 0.0

        self._connect_serial()
        self.create_timer(0.02, self.poll_serial)
        self.create_timer(0.05, self.watchdog)

    def _connect_serial(self) -> None:
        if serial is None:
            self.get_logger().error('pyserial is not installed')
            return
        try:
            self._serial = serial.Serial(
                self.port, self.baudrate,
                timeout=self.serial_timeout,
                write_timeout=self.serial_timeout,
            )
            self.get_logger().info(f'Connected to {self.port} at {self.baudrate} baud')
        except serial.SerialException as exc:
            self.get_logger().error(f'Cannot open serial port {self.port}: {exc}')

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
            if not raw:
                return
            fields = raw.decode('ascii').strip().split(',')
            if len(fields) < 3 or fields[0] != 'FB':
                return
            left_ticks, right_ticks = int(fields[1]), int(fields[2])
            self.update_odometry(left_ticks, right_ticks)
            self.publish_auxiliary_feedback(fields)
        except (serial.SerialException, UnicodeDecodeError, ValueError) as exc:
            self.get_logger().warning(f'Unable to parse feedback: {exc}')

    def publish_auxiliary_feedback(self, fields: list[str]) -> None:
        stamp = self.get_clock().now().to_msg()
        if len(fields) >= 5:
            battery = BatteryState()
            battery.header.stamp = stamp
            battery.voltage = float(fields[4])
            battery.present = battery.voltage > 0.0
            self.battery_pub.publish(battery)
        if len(fields) >= 6:
            self.estop_pub.publish(Bool(data=bool(int(fields[5]))))
        if len(fields) >= 13 and bool(int(fields[12])):
            imu = Imu()
            imu.header.stamp = stamp
            imu.header.frame_id = self.imu_frame
            imu.linear_acceleration.x = float(fields[7])
            imu.linear_acceleration.y = float(fields[8])
            imu.linear_acceleration.z = float(fields[9])
            imu.angular_velocity.x = float(fields[10])
            imu.angular_velocity.y = float(fields[11])
            imu.angular_velocity.z = float(fields[3])
            imu.orientation_covariance[0] = -1.0
            imu.angular_velocity_covariance = [0.02, 0.0, 0.0, 0.0, 0.02, 0.0, 0.0, 0.0, 0.02]
            imu.linear_acceleration_covariance = [0.1, 0.0, 0.0, 0.0, 0.1, 0.0, 0.0, 0.0, 0.1]
            self.imu_pub.publish(imu)

    def update_odometry(self, left_ticks: int, right_ticks: int) -> None:
        now = self.get_clock().now()
        if self._last_left_ticks is None:
            self._last_left_ticks, self._last_right_ticks = left_ticks, right_ticks
            self._last_feedback_time = now
            return
        dt = max((now - self._last_feedback_time).nanoseconds * 1e-9, 1e-6)
        dlt = left_ticks - self._last_left_ticks
        drt = right_ticks - self._last_right_ticks
        meters_per_tick = 2.0 * math.pi * self.wheel_radius / self.ticks_per_revolution
        dl, dr = dlt * meters_per_tick, drt * meters_per_tick
        ds = 0.5 * (dr + dl)
        dtheta = (dr - dl) / self.wheel_separation
        heading_mid = self._yaw + 0.5 * dtheta
        self._x += ds * math.cos(heading_mid)
        self._y += ds * math.sin(heading_mid)
        self._yaw = math.atan2(math.sin(self._yaw + dtheta), math.cos(self._yaw + dtheta))

        q = Quaternion(z=math.sin(self._yaw * 0.5), w=math.cos(self._yaw * 0.5))
        stamp = now.to_msg()
        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_footprint'
        odom.pose.pose.position.x = self._x
        odom.pose.pose.position.y = self._y
        odom.pose.pose.orientation = q
        odom.twist.twist.linear.x = ds / dt
        odom.twist.twist.angular.z = dtheta / dt
        self.odom_pub.publish(odom)

        joints = JointState()
        joints.header.stamp = stamp
        joints.name = ['left_wheel_joint', 'right_wheel_joint']
        joints.position = [left_ticks * 2.0 * math.pi / self.ticks_per_revolution,
                           right_ticks * 2.0 * math.pi / self.ticks_per_revolution]
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

        self._last_left_ticks, self._last_right_ticks = left_ticks, right_ticks
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
