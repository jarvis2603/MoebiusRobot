# Moebius Web UI

Responsive React + Bootstrap dashboard connected to ROS 2 through `rosbridge_websocket`.

## Features

- rosbridge connection status and reconnect button
- mecanum teleoperation: forward/reverse, strafe left/right, rotate
- keyboard controls: `W/S`, `A/D`, `Q/E`
- configurable linear and angular velocity limits
- odometry display from `/odom`
- battery voltage and percentage from `/battery_state`
- E-stop indication from `/emergency_stop`
- zero-velocity command on key/button release, browser blur and disconnect
- responsive desktop/tablet/mobile layout

## ROS 2 computer

Install dependencies on Ubuntu 24.04 / ROS 2 Jazzy:

```bash
sudo apt update
sudo apt install ros-jazzy-rosbridge-server
```

Build and source the workspace:

```bash
cd ros2_ws
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

Start the robot driver and rosbridge in separate terminals:

```bash
ros2 launch moebius_base_driver base_driver.launch.py port:=/dev/ttyUSB0
ros2 launch moebius_base_driver web_bridge.launch.py
```

Port `9090/tcp` must be reachable from the browser device. Restrict it to the robot LAN; do not expose rosbridge directly to the public internet.

## React development setup

```bash
cd web_ui
cp .env.example .env
npm install
npm run dev
```

Open:

```text
http://ROBOT_IP:5173
```

Set the robot IP in `.env`:

```dotenv
VITE_ROSBRIDGE_URL=ws://192.168.1.42:9090
```

Restart Vite after changing `.env`.

## Production build

```bash
npm run build
npm run preview
```

The static output is written to `web_ui/dist`. It can be served by Nginx, Caddy, Apache, a container or any static web server.

## ROS topics

| Direction | Topic | Type |
|---|---|---|
| UI to ROS | `/cmd_vel` | `geometry_msgs/msg/Twist` |
| ROS to UI | `/odom` | `nav_msgs/msg/Odometry` |
| ROS to UI | `/battery_state` | `sensor_msgs/msg/BatteryState` |
| ROS to UI | `/emergency_stop` | `std_msgs/msg/Bool` |

Topic names can be changed through `VITE_*` variables in `.env`.

## Safety notes

The browser is not a safety controller. STM32 command timeout and physical E-stop remain mandatory. The firmware must force motor outputs to zero when serial commands stop. Use HTTPS/WSS and authentication when the UI is accessed beyond a trusted local network.
