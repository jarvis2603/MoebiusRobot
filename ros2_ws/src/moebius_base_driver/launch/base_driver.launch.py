from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    default_config = str(
        Path(get_package_share_directory('moebius_base_driver'))
        / 'config'
        / 'base_driver.yaml'
    )

    return LaunchDescription([
        DeclareLaunchArgument('params_file', default_value=default_config),
        DeclareLaunchArgument('port', default_value='/dev/ttyACM0'),
        Node(
            package='moebius_base_driver',
            executable='base_driver',
            name='moebius_base_driver',
            output='screen',
            parameters=[
                LaunchConfiguration('params_file'),
                {'port': LaunchConfiguration('port')},
            ],
        ),
    ])
