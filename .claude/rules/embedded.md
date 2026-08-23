# Embedded Robotics Rule

Targets include STM32 and ESP32-S3, normally built with PlatformIO.

Keep deterministic control on MCU: motor PWM/direction, encoder acquisition, wheel PID, actuator timing, watchdog, battery monitoring and immediate E-stop response.

Use explicit units and rates. Avoid blocking delays in control paths. Separate scheduler rates for motor control, sensors, telemetry, OLED and diagnostics.

Serial/CAN protocols intended for deployment must be versioned and include length/type, sequence/timestamp where useful, validation and CRC/checksum. Loss of valid commands must stop motion.

Encoder calculations must document PPR semantics, quadrature factor and gearbox location. Validate motor and encoder polarity independently per wheel.

For STM32 pin changes, cross-check alternate functions, timers, ADC, I2C/UART conflicts, SWD/JTAG pins and board schematic. For ESP32-S3 check voltage level, boot/strapping pins and peripheral ownership.

Do not infer safe voltage/current limits from module names. Require datasheet/schematic evidence.