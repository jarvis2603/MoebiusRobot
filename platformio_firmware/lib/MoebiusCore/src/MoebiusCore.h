#pragma once

#include <Arduino.h>
#include <Wire.h>

namespace moebius {

struct RobotConfig {
  float wheel_radius_m{0.040f};
  float wheel_separation_m{0.260f};
  float counts_per_rev{1300.0f};
  float max_rpm{245.0f};
  float kp{6.2f};
  float ki{0.8f};
  float kd{0.2f};
  uint32_t command_timeout_ms{300};
};

class PidController {
 public:
  PidController(float kp, float ki, float kd, float output_limit = 255.0f);
  float update(float target, float measured, float dt);
  void reset();
 private:
  float kp_, ki_, kd_, limit_, integral_{0.0f}, previous_error_{0.0f};
};

class MotorDriver {
 public:
  MotorDriver(uint32_t pwm_pin, uint32_t dir_pin, bool invert = false);
  void begin();
  void write(float command);
  void stop();
 private:
  uint32_t pwm_pin_, dir_pin_;
  bool invert_;
};

class QuadratureEncoder {
 public:
  QuadratureEncoder(uint32_t pin_a, uint32_t pin_b, bool invert = false);
  void begin(void (*isr)());
  void handleInterrupt();
  int32_t read() const;
  void write(int32_t value);
 private:
  uint32_t pin_a_, pin_b_;
  bool invert_;
  volatile int32_t ticks_{0};
};

struct ImuSample {
  float ax{0.0f}, ay{0.0f}, az{0.0f};
  float gx{0.0f}, gy{0.0f}, gz{0.0f};
  float temperature_c{0.0f};
  bool valid{false};
};

class Mpu6050 {
 public:
  explicit Mpu6050(TwoWire &wire, uint8_t address = 0x68);
  bool begin();
  bool read(ImuSample &sample);
 private:
  bool writeRegister(uint8_t reg, uint8_t value);
  bool readRegisters(uint8_t reg, uint8_t *data, size_t length);
  TwoWire &wire_;
  uint8_t address_;
};

struct VelocityCommand {
  float linear_mps{0.0f};
  float angular_rps{0.0f};
  bool valid{false};
};

class SerialProtocol {
 public:
  explicit SerialProtocol(Stream &stream);
  bool poll(VelocityCommand &command);
  void publishFeedback(int32_t left_ticks, int32_t right_ticks,
                       const ImuSample &imu, float battery_v,
                       bool estop, uint32_t stamp_ms);
 private:
  bool parseLine(const String &line, VelocityCommand &command);
  Stream &stream_;
  String line_;
};

}  // namespace moebius
