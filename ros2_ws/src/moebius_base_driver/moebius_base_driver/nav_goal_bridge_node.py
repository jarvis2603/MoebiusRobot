#!/usr/bin/env python3

import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from rclpy.node import Node
from std_msgs.msg import Empty, String


class NavGoalBridge(Node):
    """Translate simple web topics into the Nav2 NavigateToPose action."""

    def __init__(self) -> None:
        super().__init__('nav_goal_bridge')
        self.client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.goal_handle = None
        self.status_pub = self.create_publisher(String, '/web_navigation/status', 10)
        self.create_subscription(PoseStamped, '/web_navigation/goal', self.goal_callback, 10)
        self.create_subscription(Empty, '/cancel_navigation', self.cancel_callback, 10)

    def publish_status(self, text: str) -> None:
        self.status_pub.publish(String(data=text))

    def goal_callback(self, pose: PoseStamped) -> None:
        if not self.client.wait_for_server(timeout_sec=0.5):
            self.publish_status('Nav2 action server unavailable')
            return
        goal = NavigateToPose.Goal()
        goal.pose = pose
        future = self.client.send_goal_async(goal, feedback_callback=self.feedback_callback)
        future.add_done_callback(self.goal_response_callback)
        self.publish_status('Sending goal')

    def goal_response_callback(self, future) -> None:
        self.goal_handle = future.result()
        if not self.goal_handle.accepted:
            self.publish_status('Goal rejected')
            return
        self.publish_status('Goal accepted')
        result_future = self.goal_handle.get_result_async()
        result_future.add_done_callback(self.result_callback)

    def feedback_callback(self, feedback_msg) -> None:
        distance = feedback_msg.feedback.distance_remaining
        self.publish_status(f'Navigating · {distance:.2f} m remaining')

    def result_callback(self, future) -> None:
        status = future.result().status
        self.publish_status(f'Navigation finished · status {status}')
        self.goal_handle = None

    def cancel_callback(self, msg: Empty) -> None:
        del msg
        if self.goal_handle is not None:
            self.goal_handle.cancel_goal_async()
            self.publish_status('Cancel requested')
        else:
            self.client.async_cancel_all_goals()
            self.publish_status('Cancel all requested')


def main(args=None) -> None:
    rclpy.init(args=args)
    node = NavGoalBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
