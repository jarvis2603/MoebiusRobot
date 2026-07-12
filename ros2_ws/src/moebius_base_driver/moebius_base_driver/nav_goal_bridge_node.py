#!/usr/bin/env python3

import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from rclpy.node import Node
from std_msgs.msg import Bool, Empty, String


class NavGoalBridge(Node):
    """Translate simple web topics into NavigateToPose with mode interlocks."""

    def __init__(self) -> None:
        super().__init__('nav_goal_bridge')
        self.client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.goal_handle = None
        self.robot_started = False
        self.robot_mode = 'manual'
        self.status_pub = self.create_publisher(String, '/web_navigation/status', 10)
        self.create_subscription(PoseStamped, '/web_navigation/goal', self.goal_callback, 10)
        self.create_subscription(Empty, '/cancel_navigation', self.cancel_callback, 10)
        self.create_subscription(Bool, '/robot/started', self.started_callback, 10)
        self.create_subscription(String, '/robot/mode', self.mode_callback, 10)

    def publish_status(self, text: str) -> None:
        self.status_pub.publish(String(data=text))

    def started_callback(self, msg: Bool) -> None:
        self.robot_started = msg.data
        if not msg.data:
            self.cancel_active_goal('Robot stopped')

    def mode_callback(self, msg: String) -> None:
        self.robot_mode = msg.data
        if msg.data != 'auto':
            self.cancel_active_goal('Manual mode')

    def goal_callback(self, pose: PoseStamped) -> None:
        if not self.robot_started or self.robot_mode != 'auto':
            self.publish_status('Goal blocked: robot must be started in auto mode')
            return
        if not self.client.wait_for_server(timeout_sec=0.5):
            self.publish_status('Nav2 action server unavailable')
            return
        if self.goal_handle is not None:
            self.goal_handle.cancel_goal_async()
        goal = NavigateToPose.Goal()
        goal.pose = pose
        future = self.client.send_goal_async(goal, feedback_callback=self.feedback_callback)
        future.add_done_callback(self.goal_response_callback)
        self.publish_status('Sending goal')

    def goal_response_callback(self, future) -> None:
        self.goal_handle = future.result()
        if not self.goal_handle.accepted:
            self.goal_handle = None
            self.publish_status('Goal rejected')
            return
        self.publish_status('Goal accepted')
        self.goal_handle.get_result_async().add_done_callback(self.result_callback)

    def feedback_callback(self, feedback_msg) -> None:
        distance = feedback_msg.feedback.distance_remaining
        self.publish_status(f'Navigating · {distance:.2f} m remaining')

    def result_callback(self, future) -> None:
        status = future.result().status
        self.publish_status(f'Navigation finished · status {status}')
        self.goal_handle = None

    def cancel_active_goal(self, reason: str = 'Cancel requested') -> None:
        if self.goal_handle is not None:
            self.goal_handle.cancel_goal_async()
            self.publish_status(reason)
        else:
            self.publish_status('No active goal')

    def cancel_callback(self, msg: Empty) -> None:
        del msg
        self.cancel_active_goal()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = NavGoalBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.cancel_active_goal('Node shutdown')
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
