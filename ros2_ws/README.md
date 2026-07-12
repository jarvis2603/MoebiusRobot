# MoebiusRobot ROS 2 Jazzy workspace

This workspace adds a ROS 2 Jazzy serial bridge without modifying the original embedded firmware tree.

## Supported interfaces

- subscribes: `/cmd_vel` (`geometry_msgs/msg/Twist`)
- publishes: `/odom` (`nav_msgs/msg/Odometry`)
- publishes: `/joint_states` (`sensor_msgs/msg/JointState`)
- broadcasts: `odom -> base_footprint`

## Paired controller firmware

The matching STM32F103RCT6 PlatformIO project is located at `../platformio_firmware`.
It uses USART1 on PA9/PA10 at 115200 baud and is configured for ST-Link upload/debug.

## Serial protocol

Host to MCU:

```text
CMD,<linear_mps>,<angular_rps>\n
```

MCU to host:

```text
FB,<left_encoder_ticks>,<right_encoder_ticks>,<gyro_z>,<battery_voltage>\n
```

Only encoder fields are consumed by the first driver version. A CRC/checksum, sequence number, emergency-stop state, and firmware timestamp should be added before competition or outdoor deployment.

## Build on Ubuntu 24.04 / ROS 2 Jazzy

```bash
source /opt/ros/jazzy/setup.bash
cd ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

## Build the STM32 firmware

```bash
cd platformio_firmware
pio run
pio run --target upload
```

## Run

Use `/dev/ttyUSB0` when USART1 is connected through a USB-to-TTL adapter, or change it to the actual device:

```bash
ros2 launch moebius_base_driver base_driver.launch.py port:=/dev/ttyUSB0
```

Test command with the wheels lifted safely from the floor:

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.05}, angular: {z: 0.0}}"
```

Inspect feedback:

```bash
ros2 topic echo /odom
ros2 topic echo /joint_states
```

## Parameters

Edit `src/moebius_base_driver/config/base_driver.yaml` and the matching constants in `platformio_firmware/src/main.cpp`:

- `wheel_radius`
- `wheel_separation`
- `ticks_per_revolution`
- left/right encoder polarity
- `port`
- `baudrate`
- `command_timeout`

The default dimensions and pin assignments are placeholders and must be verified against the real controller schematic before trusting odometry or driving the robot.
