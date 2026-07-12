# MoebiusRobot production architecture

## Scope

This branch converts the legacy RT-Thread/ROS 1 controller into a ROS 2 Jazzy-compatible four-wheel mecanum platform while preserving the original board hardware.

## Firmware layers

1. **Board support** — `HardwareConfig.h`, clocks, GPIO, USART1, I2C2, ADC and ST-Link/SWD.
2. **Drivers** — TB6612 motor channels, four quadrature encoders, MPU6050, HMC5883L, OLED and battery ADC.
3. **Control** — four independent wheel PID loops at 100 Hz, saturation, anti-windup and command ramp limiting.
4. **Kinematics** — mecanum inverse kinematics for commands and forward kinematics for encoder odometry.
5. **Safety** — boot-safe outputs, command watchdog, low-battery inhibit, invalid-command rejection and fault latching.
6. **Protocol** — versioned ASCII protocol for commissioning, followed by a CRC-protected binary protocol for deployment.
7. **Application** — deterministic cooperative scheduler; display and diagnostics never block the motor loop.

## Hardware map derived from the schematic

- MCU: STM32F103RCT6
- ROS link: CH340 to USART1, PA9/PA10
- I2C2: PB10/PB11
- IMU: MPU6050 at 0x68
- Magnetometer: HMC5883L at 0x1E
- Optional OLED: SSD1306 at 0x3C on the same I2C2 bus
- Battery divider: PA5, nominal 10 kOhm / 1 kOhm
- Motor drivers: two TB6612FNG devices, four motor channels
- Encoders: four A/B quadrature headers

## Runtime states

`BOOT -> SELF_TEST -> DISARMED -> ARMED -> FAULT`

Motors may only be energized in `ARMED`. Any command timeout, critical battery voltage, invalid encoder rate or explicit emergency-stop command returns the system to `DISARMED` or `FAULT`.

## ROS 2 interfaces

Subscriptions:

- `/cmd_vel` (`geometry_msgs/msg/Twist`), including `linear.y` for mecanum motion
- `/motor_enable` (`std_msgs/msg/Bool`)

Publications:

- `/odom` (`nav_msgs/msg/Odometry`)
- `/joint_states` (`sensor_msgs/msg/JointState`) for four wheel joints
- `/imu/data_raw` (`sensor_msgs/msg/Imu`)
- `/imu/mag` (`sensor_msgs/msg/MagneticField`)
- `/battery_state` (`sensor_msgs/msg/BatteryState`)
- `/emergency_stop` (`std_msgs/msg/Bool`)
- `/diagnostics` (`diagnostic_msgs/msg/DiagnosticArray`)

TF:

- `odom -> base_footprint`

For production localization, disable raw wheel TF and let `robot_localization` publish the fused `odom -> base_footprint` transform.

## Protocol roadmap

### Commissioning protocol

Human-readable newline-delimited frames:

- `CMD,vx,vy,wz,enable,sequence`
- `SYS,IP,address`
- `FB2,sequence,mcu_ms,state,battery,fl,fr,rl,rr,ax,ay,az,gx,gy,gz,mx,my,mz,error_flags`

### Deployment protocol

Binary frames must include:

- sync word
- protocol version
- message type
- payload length
- monotonically increasing sequence number
- MCU timestamp
- CRC-16/CCITT

The ASCII protocol remains available behind a compile-time commissioning flag.

## Timing budget

- wheel control: 100 Hz
- encoder sampling: 100 Hz
- ROS feedback/odometry: 50 Hz
- IMU: 50 Hz
- magnetometer: 20 Hz
- OLED: 2 Hz
- battery: 5 Hz

No display, serial formatting or I2C transaction may block the 100 Hz control deadline.

## Production gates

The branch must not be merged for field use until all of the following pass:

1. PlatformIO build for `genericSTM32F103RC`.
2. ROS 2 Jazzy `colcon build` and package tests.
3. Motor pin and wheel-order verification with the chassis lifted.
4. Encoder polarity and 1300-count calibration.
5. Battery-divider calibration against a multimeter.
6. IMU axis/orientation verification.
7. Watchdog and low-battery stop tests.
8. One-hour thermal and communication soak test.
9. Straight, lateral and rotation odometry calibration.
10. EKF/Nav2 integration test at reduced speed.
