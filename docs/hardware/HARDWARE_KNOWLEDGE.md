# Hardware Knowledge Base

This file separates verified project facts from values that still require datasheet or physical verification. Claude Code must not convert TBD entries into assumed facts.

## Compute
| Device | Role | OS/ROS | Verified interfaces | Notes |
|---|---|---|---|---|
| NVIDIA Jetson | perception/high-level ROS 2 | TBD | TBD | exact model required |
| Raspberry Pi | ROS 2 / Web / robot supervisor | Ubuntu 24.04 / Jazzy target | USB/network | exact model required |

## Low-level controllers
| Device | Toolchain | Role | Notes |
|---|---|---|---|
| STM32 | PlatformIO | deterministic motor/sensor control | exact MCU/board documented per project |
| ESP32-S3 | PlatformIO | auxiliary I/O/network/USB where required | exact board required |

## Sensors
| Device | ROS role | Interface | Frame/topic target | Verification required |
|---|---|---|---|---|
| IMU | orientation/angular velocity/acceleration | board-specific | imu_link, /imu/* | model, mounting, covariance |
| RPLIDAR A3 | 2D LaserScan | USB/serial | laser_link, /scan | mounting, scan configuration |
| RealSense D435i | RGB/depth/IMU | USB | camera frames | mounting, enabled streams, synchronization |

## Actuation
| Device | Role | Interface | Verification required |
|---|---|---|---|
| Cytron MDD10A | brushed DC motor power stage | PWM/DIR depending design | supply, current, pin mode |
| ODrive v3.6 | BLDC controller | version-dependent | firmware version, encoder, bus/API, limits |
| Motor + encoder | drive actuator | motor + quadrature | PPR semantics, gear ratio, polarity, rated output RPM |
| Hiwonder LX-16A | arm/gripper servo | half-duplex serial bus | IDs, voltage, limits, mechanical zero |

## Required interface records
For each installed device, document: part/revision, supply voltage, peak/continuous current, connector/pinout, logic level, bus, baud/bitrate/address, ROS driver/package, topic/service/action, frame_id, update rate, physical mounting transform, calibration, failure behavior and datasheet source.
