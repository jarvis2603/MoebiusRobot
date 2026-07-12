# Moebius description

Parametric ROS 2 Jazzy URDF/Xacro model of the four-wheel mecanum Moebius robot.

## Build

```bash
cd ros2_ws
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

## Display in RViz2

```bash
ros2 launch moebius_description display.launch.py
```

Without the joint-state GUI:

```bash
ros2 launch moebius_description display.launch.py use_gui:=false
```

## Dimensions to measure

Edit the properties at the beginning of `urdf/moebius_robot.urdf.xacro`:

- `wheel_radius`
- `wheel_width`
- `wheelbase`: distance between front and rear wheel centers
- `track_width`: distance between left and right wheel centers
- lower and upper chassis plate dimensions
- vertical plate gap
- LiDAR mounting height and offset

The current model uses primitive geometry so that it remains lightweight and robust in RViz2. The diagonal silver strips on each wheel are visual cues for mecanum roller orientation; they are not physical roller contact models.

## Coordinate convention

- X: forward
- Y: left
- Z: upward
- `base_footprint`: ground-projected frame
- `base_link`: chassis frame at wheel-center height
- `laser_link`: LiDAR frame
- `imu_link`: onboard IMU frame

## Validation

After building, validate the generated URDF:

```bash
xacro $(ros2 pkg prefix moebius_description)/share/moebius_description/urdf/moebius_robot.urdf.xacro > /tmp/moebius.urdf
check_urdf /tmp/moebius.urdf
```
