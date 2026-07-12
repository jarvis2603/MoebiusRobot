# Web Nav2 UI commissioning

## Start order

1. Start the STM32 base driver.
2. Start localization or SLAM so `map -> odom` is available.
3. Start Nav2 and verify `/navigate_to_pose` exists.
4. Start `web_bridge.launch.py`.
5. Start the React UI.

```bash
ros2 launch moebius_base_driver base_driver.launch.py port:=/dev/ttyUSB0
ros2 launch moebius_base_driver web_bridge.launch.py
cd web_ui && npm run dev
```

## Required checks

```bash
ros2 topic echo /map --once
ros2 topic echo /scan --once
ros2 topic echo /plan --once
ros2 topic echo /local_plan --once
ros2 topic echo /local_costmap/published_footprint --once
ros2 action list | grep navigate_to_pose
ros2 run tf2_ros tf2_echo map base_link
```

## Operating sequence

1. Connect the browser to rosbridge.
2. Press **Start Robot**. This always starts in Manual mode.
3. Test low-speed manual movement.
4. Stop the robot and verify velocity reaches zero.
5. Start again, select **Auto**, then click the map.
6. Use **Cancel goal** before returning to Manual.

The ROS-side goal bridge also rejects goals unless the robot is Started and in Auto mode.

## Topic remapping

Nav2 installations use different plan topic names. Configure the browser in `.env`:

```dotenv
VITE_PLAN_TOPIC=/plan
VITE_LOCAL_PLAN_TOPIC=/local_plan
VITE_FOOTPRINT_TOPIC=/local_costmap/published_footprint
```

Use `ros2 topic list` to find the actual names.

## LaserScan limitation

The browser overlay draws scan points directly. For exact alignment on the occupancy grid, transform the scan into the map frame on the ROS computer and publish a PointCloud2 or map-frame scan topic. Do not use the raw browser overlay for precision measurement.
