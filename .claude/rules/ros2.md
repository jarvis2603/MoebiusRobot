# ROS 2 / SLAM / Nav2 Rule

Default: Ubuntu 24.04 + ROS 2 Jazzy.

Before changing SLAM or Nav2, inspect and validate in this order:
1. /tf and /tf_static ownership
2. map -> odom -> base_footprint/base_link -> laser_link/imu_link
3. sensor frame_id and timestamps
4. /odom and wheel sign/scale
5. /scan validity and frequency
6. IMU orientation/covariance if fused
7. robot footprint and physical dimensions
8. velocity/acceleration limits
9. lifecycle state of Nav2 nodes
10. planner/controller/costmap parameters

Prefer SLAM Toolbox for 2D LiDAR mapping unless project requirements say otherwise. Use robot_localization deliberately; never allow two nodes to publish the same TF transform.

Navigation commands from Web UI should reach Nav2 through an action bridge/supervisor with robot state, AUTO mode and E-stop checks. Manual commands must be blocked in AUTO; Nav2 goals must be cancelled before MANUAL.

Use launch files, parameters and namespaces rather than hard-coded values. Preserve topic/frame consistency across URDF, drivers, EKF, SLAM, Nav2 and Web UI.