# MoebiusRobot STM32F103RCT6 firmware

PlatformIO starter firmware for the ROS 2 Jazzy base driver.

## Target

- MCU: STM32F103RCT6
- Framework: Arduino for STM32
- Upload/debug: ST-Link
- ROS communication: USART1, 115200 baud
- PlatformIO environment: `genericSTM32F103RC`

## Build and upload

```bash
cd platformio_firmware
pio run
pio run --target upload
pio device monitor
```

## Initial pin map

| Function | Pin |
|---|---|
| USART1 TX to host | PA9 |
| USART1 RX from host | PA10 |
| Left motor PWM | PA0 |
| Right motor PWM | PA1 |
| Left motor direction | PB0 |
| Right motor direction | PB1 |
| Left encoder A | PB6 |
| Right encoder A | PB7 |
| Emergency stop, active low | PB8 |
| Status LED | PC13 |

These assignments are placeholders. Compare them with the Moebius controller schematic before connecting motors or encoders.

## Serial protocol

ROS 2 to STM32:

```text
CMD,<linear_mps>,<angular_rps>\n
```

STM32 to ROS 2:

```text
FB,<left_ticks>,<right_ticks>,<gyro_z_rad_s>,<battery_voltage>\n
```

The initial firmware sends zero for IMU and battery fields until the actual sensor and ADC circuits are identified.

## Safety behavior

- Motor command timeout: 300 ms
- Active-low emergency-stop input
- Wheel-speed limit before PID control
- PWM output is forced to zero after timeout or E-stop

## Required hardware-specific work

1. Confirm motor-driver input topology. Some boards require separate `IN1/IN2` pins instead of one direction pin plus PWM.
2. Add encoder B channels and quadrature decoding. The current starter uses one interrupt channel per wheel and therefore cannot infer reverse direction from the encoder alone.
3. Replace wheel radius, wheel separation and encoder ticks per revolution with measured values in both firmware and ROS YAML.
4. Tune the left and right wheel PID gains with the robot lifted safely from the floor.
5. Add CRC, sequence numbers and explicit E-stop status before field deployment.
6. Implement the actual IMU and battery-voltage acquisition circuits.

## Electrical notes

STM32F103 GPIO uses 3.3 V logic. Do not connect a 5 V UART output directly to PA10. Ensure the motor driver and encoder outputs are compatible or level-shifted, and connect grounds between the STM32, motor driver and ROS computer interface.
