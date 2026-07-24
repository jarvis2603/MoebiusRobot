from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def include(package: str, launch_file: str, *, condition=None, arguments=None):
    source = PythonLaunchDescriptionSource(
        str(Path(get_package_share_directory(package)) / 'launch' / launch_file)
    )
    return IncludeLaunchDescription(
        source,
        condition=condition,
        launch_arguments=(arguments or {}).items(),
    )


def generate_launch_description() -> LaunchDescription:
    serial_port = LaunchConfiguration('serial_port')
    use_slam = LaunchConfiguration('use_slam')
    use_nav2 = LaunchConfiguration('use_nav2')
    use_sim_time = LaunchConfiguration('use_sim_time')
    nav2_params = LaunchConfiguration('nav2_params')

    default_nav2_params = str(
        Path(get_package_share_directory('moebius_bringup')) / 'config' / 'nav2_params.yaml'
    )

    return LaunchDescription([
        DeclareLaunchArgument('serial_port', default_value='/dev/ttyUSB0'),
        DeclareLaunchArgument('use_slam', default_value='false'),
        DeclareLaunchArgument('use_nav2', default_value='false'),
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument('nav2_params', default_value=default_nav2_params),

        include(
            'moebius_base_driver',
            'base_driver.launch.py',
            arguments={'port': serial_port},
        ),
        include('moebius_base_driver', 'web_bridge.launch.py'),
        include('moebius_description', 'display.launch.py'),

        include(
            'slam_toolbox',
            'online_async_launch.py',
            condition=IfCondition(use_slam),
            arguments={'use_sim_time': use_sim_time},
        ),
        include(
            'nav2_bringup',
            'navigation_launch.py',
            condition=IfCondition(use_nav2),
            arguments={
                'use_sim_time': use_sim_time,
                'params_file': nav2_params,
            },
        ),
    ])
