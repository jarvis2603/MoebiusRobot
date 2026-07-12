# Moebius Web UI

React + Bootstrap Nav2 console connected to ROS 2 through `rosbridge_websocket` and `ros2d.js`.

## Features

- mecanum manual teleoperation with keyboard and touch controls
- Manual/Auto mode interlock
- Start, Stop and Reset supervisor services
- ROS occupancy grid from `/map`
- click-to-goal through the Nav2 `NavigateToPose` action
- LaserScan overlay from `/scan`
- global and local path overlays
- local costmap footprint overlay
- odometry, battery and E-stop status
- velocity zeroing on release, window blur, stop and mode changes

## ROS 2 setup

```bash
sudo apt update
sudo apt install \
  ros-jazzy-rosbridge-server \
  ros-jazzy-navigation2 \
  ros-jazzy-nav2-bringup

cd ros2_ws
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

Start the base driver and web bridge:

```bash
ros2 launch moebius_base_driver base_driver.launch.py port:=/dev/ttyUSB0
ros2 launch moebius_base_driver web_bridge.launch.py
```

Start localization/SLAM and Nav2 separately. The UI expects a valid `map -> odom -> base_link` TF tree and a running `navigate_to_pose` action server.

## React setup

```bash
cd web_ui
cp .env.example .env
npm install
npm run dev
```

Open `http://ROBOT_IP:5173`. Set the ROS computer address in `.env`:

```dotenv
VITE_ROSBRIDGE_URL=ws://192.168.1.42:9090
```

## Expected interfaces

| Direction | Topic/service | Type |
|---|---|---|
| UI to ROS | `/cmd_vel` | `geometry_msgs/msg/Twist` |
| UI to bridge | `/web_navigation/goal` | `geometry_msgs/msg/PoseStamped` |
| UI to bridge | `/cancel_navigation` | `std_msgs/msg/Empty` |
| ROS to UI | `/map` | `nav_msgs/msg/OccupancyGrid` |
| ROS to UI | `/scan` | `sensor_msgs/msg/LaserScan` |
| ROS to UI | `/plan` | `nav_msgs/msg/Path` |
| ROS to UI | `/local_plan` | `nav_msgs/msg/Path` |
| ROS to UI | `/local_costmap/published_footprint` | `geometry_msgs/msg/PolygonStamped` |
| ROS to UI | `/odom` | `nav_msgs/msg/Odometry` |
| ROS to UI | `/battery_state` | `sensor_msgs/msg/BatteryState` |
| ROS to UI | `/emergency_stop` | `std_msgs/msg/Bool` |
| Service | `/robot/start` | `std_srvs/srv/Trigger` |
| Service | `/robot/stop` | `std_srvs/srv/Trigger` |
| Service | `/robot/reset` | `std_srvs/srv/Trigger` |
| Service | `/robot/set_auto_mode` | `std_srvs/srv/SetBool` |

Nav2 topic names vary by configuration. Update `.env` when your controller publishes plans or footprints under namespaced topics, for example `/controller_server/local_plan` or `/local_costmap/costmap_raw`.

## Important map notes

The occupancy grid is displayed in the map frame. Path and footprint topics should also be in the map frame or transformed before publishing. The current lightweight LaserScan overlay assumes scan coordinates are already suitable for the viewer; for accurate map-frame rendering, add a TF-aware scan projection node or publish a transformed point cloud.

## Production build

```bash
npm run build
```

Static files are written to `web_ui/dist`. Serve them with Nginx or another static server. Keep rosbridge on the trusted robot LAN and use authentication plus HTTPS/WSS outside that network.

## Safety

The browser is not a safety controller. Physical E-stop, STM32 watchdog, motor-enable logic and command timeout remain mandatory. Auto goals are rejected by the bridge unless the robot is both Started and in Auto mode.
