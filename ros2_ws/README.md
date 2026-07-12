# MoebiusRobot ROS 2 Jazzy workspace

This workspace adds a ROS 2 Jazzy serial bridge without modifying the original embedded firmware tree.

## Supported interfaces

- subscribes: `/cmd_vel` (`geometry_msgs/msg/Twist`)
- publishes: `/odom` (`nav_msgs/msg/Odometry`)
- publishes: `/joint_states` (`sensor_msgs/msg/JointState`)
- broadcasts: `odom -> base_footprint`

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

## Run

```bash
ros2 launch moebius_base_driver base_driver.launch.py port:=/dev/ttyACM0
```

Test command:

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.1}, angular: {z: 0.0}}"
```

Inspect feedback:

```bash
ros2 topic echo /odom
ros2 topic echo /joint_states
```

## Parameters

Edit `src/moebius_base_driver/config/base_driver.yaml` to match the real robot:

- `wheel_radius`
- `wheel_separation`
- `ticks_per_revolution`
- `port`
- `baudrate`
- `command_timeout`

The default dimensions are placeholders and must be measured before trusting odometry.
