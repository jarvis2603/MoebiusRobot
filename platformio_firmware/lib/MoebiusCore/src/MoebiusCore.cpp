#include "MoebiusCore.h"

#include <math.h>

namespace moebius {

PidController::PidController(float kp, float ki, float kd, float output_limit)
    : kp_(kp), ki_(ki), kd_(kd), limit_(output_limit) {}

float PidController::update(float target, float measured, float dt) {
  if (dt <= 0.0f) return 0.0f;
  const float error = target - measured;
  integral_ = constrain(integral_ + error * dt, -limit_, limit_);
  const float derivative = (error - previous_error_) / dt;
  previous_error_ = error;
  return constrain(kp_ * error + ki_ * integral_ + kd_ * derivative,
                   -limit_, limit_);
}

void PidController::reset() {
  integral_ = 0.0f;
  previous_error_ = 0.0f;
}

MotorDriver::MotorDriver(uint32_t pwm_pin, uint32_t dir_pin, bool invert)
    : pwm_pin_(pwm_pin), dir_pin_(dir_pin), invert_(invert) {}

void MotorDriver::begin() {
  pinMode(pwm_pin_, OUTPUT);
  pinMode(dir_pin_, OUTPUT);
  stop();
}

void MotorDriver::write(float command) {
  if (invert_) command = -command;
  const bool forward = command >= 0.0f;
  digitalWrite(dir_pin_, forward ? HIGH : LOW);
  analogWrite(pwm_pin_, constrain(static_cast<int>(fabsf(command)), 0, 255));
}

void MotorDriver::stop() { analogWrite(pwm_pin_, 0); }

QuadratureEncoder::QuadratureEncoder(uint32_t pin_a, uint32_t pin_b, bool invert)
    : pin_a_(pin_a), pin_b_(pin_b), invert_(invert) {}

void QuadratureEncoder::begin(void (*isr)()) {
  pinMode(pin_a_, INPUT_PULLUP);
  pinMode(pin_b_, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(pin_a_), isr, CHANGE);
}

void QuadratureEncoder::handleInterrupt() {
  const bool a = digitalRead(pin_a_);
  const bool b = digitalRead(pin_b_);
  int8_t direction = (a == b) ? 1 : -1;
  if (invert_) direction = -direction;
  ticks_ += direction;
}

int32_t QuadratureEncoder::read() const {
  noInterrupts();
  const int32_t value = ticks_;
  interrupts();
  return value;
}

void QuadratureEncoder::write(int32_t value) {
  noInterrupts();
  ticks_ = value;
  interrupts();
}

Mpu6050::Mpu6050(TwoWire &wire, uint8_t address)
    : wire_(wire), address_(address) {}

bool Mpu6050::writeRegister(uint8_t reg, uint8_t value) {
  wire_.beginTransmission(address_);
  wire_.write(reg);
  wire_.write(value);
  return wire_.endTransmission() == 0;
}

bool Mpu6050::readRegisters(uint8_t reg, uint8_t *data, size_t length) {
  wire_.beginTransmission(address_);
  wire_.write(reg);
  if (wire_.endTransmission(false) != 0) return false;
  if (wire_.requestFrom(address_, static_cast<uint8_t>(length)) != length) return false;
  for (size_t i = 0; i < length; ++i) data[i] = wire_.read();
  return true;
}

bool Mpu6050::begin() {
  uint8_t who = 0;
  if (!readRegisters(0x75, &who, 1) || (who != 0x68 && who != 0x69)) return false;
  return writeRegister(0x6B, 0x00) &&  // wake
         writeRegister(0x1A, 0x03) &&  // DLPF ~44 Hz
         writeRegister(0x1B, 0x00) &&  // gyro +-250 dps
         writeRegister(0x1C, 0x00);    // accel +-2 g
}

bool Mpu6050::read(ImuSample &sample) {
  uint8_t data[14];
  if (!readRegisters(0x3B, data, sizeof(data))) {
    sample.valid = false;
    return false;
  }
  auto s16 = [&](int i) -> int16_t {
    return static_cast<int16_t>((static_cast<uint16_t>(data[i]) << 8) | data[i + 1]);
  };
  constexpr float g = 9.80665f;
  constexpr float deg_to_rad = 0.017453292519943295f;
  sample.ax = s16(0) / 16384.0f * g;
  sample.ay = s16(2) / 16384.0f * g;
  sample.az = s16(4) / 16384.0f * g;
  sample.temperature_c = s16(6) / 340.0f + 36.53f;
  sample.gx = s16(8) / 131.0f * deg_to_rad;
  sample.gy = s16(10) / 131.0f * deg_to_rad;
  sample.gz = s16(12) / 131.0f * deg_to_rad;
  sample.valid = true;
  return true;
}

SerialProtocol::SerialProtocol(Stream &stream) : stream_(stream) { line_.reserve(96); }

bool SerialProtocol::parseLine(const String &line, VelocityCommand &command) {
  if (!line.startsWith("CMD,")) return false;
  const int comma = line.indexOf(',', 4);
  if (comma < 0) return false;
  const float linear = line.substring(4, comma).toFloat();
  const float angular = line.substring(comma + 1).toFloat();
  if (!isfinite(linear) || !isfinite(angular)) return false;
  command.linear_mps = linear;
  command.angular_rps = angular;
  command.valid = true;
  return true;
}

bool SerialProtocol::poll(VelocityCommand &command) {
  while (stream_.available()) {
    const char c = static_cast<char>(stream_.read());
    if (c == '\n') {
      line_.trim();
      const bool ok = parseLine(line_, command);
      line_ = "";
      if (ok) return true;
    } else if (c != '\r' && line_.length() < 95) {
      line_ += c;
    }
  }
  return false;
}

void SerialProtocol::publishFeedback(int32_t left_ticks, int32_t right_ticks,
                                     const ImuSample &imu, float battery_v,
                                     bool estop, uint32_t stamp_ms) {
  stream_.print("FB,");
  stream_.print(left_ticks); stream_.print(',');
  stream_.print(right_ticks); stream_.print(',');
  stream_.print(imu.gz, 6); stream_.print(',');
  stream_.print(battery_v, 3); stream_.print(',');
  stream_.print(estop ? 1 : 0); stream_.print(',');
  stream_.print(stamp_ms); stream_.print(',');
  stream_.print(imu.ax, 6); stream_.print(',');
  stream_.print(imu.ay, 6); stream_.print(',');
  stream_.print(imu.az, 6); stream_.print(',');
  stream_.print(imu.gx, 6); stream_.print(',');
  stream_.print(imu.gy, 6); stream_.print(',');
  stream_.println(imu.valid ? 1 : 0);
}

}  // namespace moebius
