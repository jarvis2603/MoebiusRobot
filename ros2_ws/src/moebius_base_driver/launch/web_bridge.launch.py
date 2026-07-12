from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    port = LaunchConfiguration('port')
    address = LaunchConfiguration('address')

    return LaunchDescription([
        DeclareLaunchArgument('port', default_value='9090'),
        DeclareLaunchArgument('address', default_value='0.0.0.0'),
        Node(
            package='moebius_base_driver',
            executable='robot_control',
            name='robot_control',
            output='screen',
        ),
        Node(
            package='rosbridge_server',
            executable='rosbridge_websocket',
            name='rosbridge_websocket',
            output='screen',
            parameters=[{
                'port': port,
                'address': address,
                'fragment_timeout': 600,
                'delay_between_messages': 0.0,
                'max_message_size': 10000000,
                'unregister_timeout': 10.0,
                'use_compression': False,
            }],
        ),
    ])
