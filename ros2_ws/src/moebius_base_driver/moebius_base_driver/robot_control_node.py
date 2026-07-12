#!/usr/bin/env python3

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from std_msgs.msg import Bool, Empty, String
from std_srvs.srv import SetBool, Trigger


class RobotControlNode(Node):
    """Safety-oriented supervisory state for the web UI and Nav2."""

    def __init__(self) -> None:
        super().__init__('robot_control')
        self.started = False
        self.mode = 'manual'
        self.started_pub = self.create_publisher(Bool, '/robot/started', 10)
        self.mode_pub = self.create_publisher(String, '/robot/mode', 10)
        self.motor_enable_pub = self.create_publisher(Bool, '/motor_enable', 10)
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.cancel_pub = self.create_publisher(Empty, '/cancel_navigation', 10)
        self.create_service(Trigger, '/robot/start', self.start_callback)
        self.create_service(Trigger, '/robot/stop', self.stop_callback)
        self.create_service(Trigger, '/robot/reset', self.reset_callback)
        self.create_service(SetBool, '/robot/set_auto_mode', self.mode_callback)
        self.create_timer(0.5, self.publish_state)
        self.publish_state()

    def zero_velocity(self) -> None:
        self.cmd_vel_pub.publish(Twist())

    def publish_state(self) -> None:
        self.started_pub.publish(Bool(data=self.started))
        self.mode_pub.publish(String(data=self.mode))
        self.motor_enable_pub.publish(Bool(data=self.started))

    def start_callback(self, request, response):
        del request
        self.started = True
        self.mode = 'manual'
        self.publish_state()
        response.success = True
        response.message = 'Robot started in manual mode'
        return response

    def stop_callback(self, request, response):
        del request
        self.zero_velocity()
        self.cancel_pub.publish(Empty())
        self.started = False
        self.mode = 'manual'
        self.publish_state()
        response.success = True
        response.message = 'Robot stopped and navigation cancelled'
        return response

    def reset_callback(self, request, response):
        del request
        self.zero_velocity()
        self.cancel_pub.publish(Empty())
        self.started = False
        self.mode = 'manual'
        self.publish_state()
        response.success = True
        response.message = 'Supervisor reset; hardware reset is not asserted'
        return response

    def mode_callback(self, request, response):
        if request.data and not self.started:
            response.success = False
            response.message = 'Start the robot before enabling auto mode'
            return response
        self.zero_velocity()
        self.mode = 'auto' if request.data else 'manual'
        if self.mode == 'manual':
            self.cancel_pub.publish(Empty())
        self.publish_state()
        response.success = True
        response.message = f'Mode set to {self.mode}'
        return response


def main(args=None) -> None:
    rclpy.init(args=args)
    node = RobotControlNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.zero_velocity()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
