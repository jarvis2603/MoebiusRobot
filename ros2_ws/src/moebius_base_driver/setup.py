from setuptools import find_packages, setup

package_name = 'moebius_base_driver'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/base_driver.launch.py']),
        ('share/' + package_name + '/config', ['config/base_driver.yaml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='jarvis2603',
    maintainer_email='jarvis2603@users.noreply.github.com',
    description='ROS 2 Jazzy serial base driver for MoebiusRobot.',
    license='MIT',
    entry_points={
        'console_scripts': [
            'base_driver = moebius_base_driver.base_driver:main',
        ],
    },
)
