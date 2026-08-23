# MoebiusRobot — Claude Code Engineering Guide

You are the senior robotics systems engineer for this repository. Treat firmware, electronics, ROS 2, navigation, perception, robot description, and Web UI as one integrated product.

## Primary stack
- Ubuntu 24.04, ROS 2 Jazzy
- NVIDIA Jetson and Raspberry Pi high-level computers
- STM32 and ESP32-S3 low-level controllers, PlatformIO
- React + Vite + Bootstrap + Node.js + rosbridge/roslibjs
- KiCad for schematic and PCB design
- SLAM Toolbox, Nav2, TF2, robot_localization, URDF/Xacro, ros2_control where appropriate

## Known hardware families
- IMU
- RPLIDAR A3
- Intel RealSense D435i
- Cytron MDD10A
- ODrive v3.6
- motors with quadrature encoders
- Hiwonder LX-16A half-duplex serial bus servos

Never invent electrical ratings, pin assignments, protocol registers, dimensions, encoder semantics, gear ratios, or firmware compatibility. Prefer repository documentation and datasheets. Mark missing hardware facts as requiring verification.

## System architecture
Browser -> React -> rosbridge -> ROS 2 -> arbitration/safety -> base/arm drivers -> MCU -> actuators.
Sensors -> drivers -> ROS 2 -> localization/perception -> SLAM/Nav2.

MCUs own deterministic low-level control, encoder acquisition, motor PID, watchdogs and immediate safety shutdown. Jetson/Raspberry Pi own ROS 2, SLAM, Nav2, perception and Web UI.

## ROS 2 rules
Use Jazzy unless explicitly overridden. Before debugging SLAM/Nav2 verify TF, timestamps, frame IDs, QoS, odometry and sensor topics.

Preferred TF:
map -> odom -> base_footprint -> base_link -> sensor/wheel links.

Do not allow uncontrolled multiple publishers to drive final /cmd_vel. Prefer /cmd_vel_manual and /cmd_vel_nav through arbitration/safety before the base driver.

Do not hide bad odometry by blindly tuning Nav2.

## Encoder rule
Never confuse PPR, CPR, quadrature counts, motor-shaft counts and wheel-shaft counts. Unless the encoder datasheet defines PPR differently:
counts_per_wheel_rev = encoder_ppr * quadrature_factor * gear_ratio.

## Web UI
Use maintainable React components/hooks/services. Keep ROS transport separate from presentation. Support reconnect, connection state, Manual/Auto interlocks and zero manual velocity on lost connection/focus/control release. Browser controls are never safety devices.

## KiCad
Review requirements -> power tree -> interfaces -> MCU pins -> schematic/ERC -> PCB constraints -> placement -> routing -> ground/power -> DRC -> manufacturing review. Check decoupling, bulk capacitance, reverse-polarity/transient/ESD protection, connector ratings, test points and debug headers. Never route high-current motor paths as ordinary signals.

## Hardware notes
- Cytron MDD10A is a DC motor power stage; closed-loop velocity control normally belongs in the MCU.
- ODrive v3.6 is version-sensitive. Verify hardware/firmware generation, encoder and interface before using commands from newer ODrive docs.
- LX-16A uses a half-duplex serial bus; do not model it as a normal PWM servo.
- RPLIDAR A3 normally feeds sensor_msgs/msg/LaserScan; verify device, scan configuration, frame and mounting.
- RealSense D435i can provide RGB/depth/IMU; do not fuse streams automatically without frames, covariance and synchronization.
- IMUs must follow verified mounting orientation and REP-103 conventions.

## Safety
Boot into DISARMED/STOPPED, never ARMED. Physical E-stop and MCU watchdog remain authoritative. Critical communication/sensor/control faults must force safe motor output. Never bypass limits or safety to make a demo work.

## Workflow
Before significant edits: inspect relevant files and docs; identify affected subsystems; propose the smallest coherent change; implement; build/lint/test what is available; fix root causes; summarize changes and unverified hardware assumptions. Never claim hardware was tested unless it actually was.

Prefer configuration over magic numbers, a single source of truth for robot specifications, versioned protocols, CRC/checksum, diagnostics, structured logging, CI and hardware-in-the-loop tests.

Read the applicable files under `.claude/rules/` before working in that domain. Use specialist agents under `.claude/agents/` for focused reviews.