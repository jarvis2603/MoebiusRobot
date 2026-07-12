from glob import glob
import os

from setuptools import find_packages, setup

package_name = 'moebius_base_driver'

setup(
    name=package_name,
    version='0.3.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='jarvis2603',
    maintainer_email='jarvis2603@users.noreply.github.com',
    description='ROS 2 Jazzy mecanum serial driver and web supervisor for MoebiusRobot.',
    license='MIT',
    entry_points={
        'console_scripts': [
            'base_driver = moebius_base_driver.base_driver_node:main',
            'robot_control = moebius_base_driver.robot_control_node:main',
        ],
    },
)
