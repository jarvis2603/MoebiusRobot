# Robotics Integration Review Checklist

## Architecture
- [ ] Command and sensor data flows are documented.
- [ ] Safety ownership is explicit.
- [ ] Robot constants have one authoritative source.

## Hardware / PCB
- [ ] Power/current budget verified.
- [ ] Pinout and logic levels verified.
- [ ] Protection/decoupling/grounding reviewed.
- [ ] ERC/DRC completed for PCB changes.

## Firmware
- [ ] Watchdog and safe startup tested.
- [ ] Motor and encoder polarity verified per wheel.
- [ ] Encoder PPR/quadrature/gear ratio documented.
- [ ] Protocol validation/CRC and timeout behavior tested.

## ROS 2
- [ ] TF has one publisher per transform.
- [ ] /odom scale/sign/rate verified.
- [ ] Sensor frame IDs/timestamps/QoS verified.
- [ ] EKF inputs and covariance justified.

## SLAM / Nav2
- [ ] /scan and laser transform valid.
- [ ] Footprint matches physical robot.
- [ ] Velocity/acceleration limits match hardware.
- [ ] Costmaps/planner/controller tested at low speed.
- [ ] Manual and autonomous velocity sources are arbitrated.

## Web UI
- [ ] Reconnect and cleanup tested.
- [ ] Connection loss commands zero velocity.
- [ ] MANUAL/AUTO/STOP/FAULT/ESTOP interlocks enforced server-side/ROS-side.
- [ ] Navigation feedback/cancel works.

## Deployment
- [ ] systemd startup/shutdown/restart tested.
- [ ] Logs and diagnostics available.
- [ ] Web production build/reverse proxy tested.
- [ ] Recovery after ROS/MCU/network failure tested.

## Final review
- [ ] Run the system-reviewer agent across PCB -> firmware -> ROS -> navigation -> Web UI.
- [ ] Clearly list all items requiring real-hardware verification before merge/release.
