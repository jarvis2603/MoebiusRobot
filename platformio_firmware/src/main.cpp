#include <Arduino.h>
#include <Wire.h>
#include <MoebiusCore.h>

using namespace moebius;

namespace pins {
constexpr PinName ROS_RX = PA_10;
constexpr PinName ROS_TX = PA_9;
constexpr uint32_t LEFT_PWM = PA0;
constexpr uint32_t RIGHT_PWM = PA1;
constexpr uint32_t LEFT_DIR = PB0;
constexpr uint32_t RIGHT_DIR = PB1;
constexpr uint32_t LEFT_ENC_A = PB6;
constexpr uint32_t LEFT_ENC_B = PB5;
constexpr uint32_t RIGHT_ENC_A = PB7;
constexpr uint32_t RIGHT_ENC_B = PB4;  // JTAG pin: disable full JTAG if required.
constexpr uint32_t ESTOP_IN = PB8;
constexpr uint32_t STATUS_LED = PC13;
constexpr uint32_t I2C2_SDA = PB11;
constexpr uint32_t I2C2_SCL = PB10;
}  // namespace pins

namespace timing {
constexpr uint32_t BAUD = 115200;
constexpr uint32_t CONTROL_PERIOD_MS = 10;   // 100 Hz motor PID
constexpr uint32_t FEEDBACK_PERIOD_MS = 20;  // 50 Hz encoder/IMU feedback
constexpr uint32_t IMU_PERIOD_MS = 20;       // 50 Hz
}  // namespace timing

RobotConfig robot;
HardwareSerial RosSerial(pins::ROS_RX, pins::ROS_TX);
TwoWire ImuWire(pins::I2C2_SDA, pins::I2C2_SCL);

MotorDriver left_motor(pins::LEFT_PWM, pins::LEFT_DIR, false);
MotorDriver right_motor(pins::RIGHT_PWM, pins::RIGHT_DIR, false);
QuadratureEncoder left_encoder(pins::LEFT_ENC_A, pins::LEFT_ENC_B, false);
QuadratureEncoder right_encoder(pins::RIGHT_ENC_A, pins::RIGHT_ENC_B, false);
PidController left_pid(robot.kp, robot.ki, robot.kd);
PidController right_pid(robot.kp, robot.ki, robot.kd);
Mpu6050 imu(ImuWire);
SerialProtocol protocol(RosSerial);

ImuSample imu_sample;
float target_left_rad_s = 0.0f;
float target_right_rad_s = 0.0f;
int32_t previous_left_ticks = 0;
int32_t previous_right_ticks = 0;
uint32_t last_command_ms = 0;
uint32_t last_control_ms = 0;
uint32_t last_feedback_ms = 0;
uint32_t last_imu_ms = 0;
bool imu_available = false;

void leftEncoderIsr() { left_encoder.handleInterrupt(); }
void rightEncoderIsr() { right_encoder.handleInterrupt(); }

bool emergencyStopActive() { return digitalRead(pins::ESTOP_IN) == LOW; }

void stopMotors() {
  target_left_rad_s = 0.0f;
  target_right_rad_s = 0.0f;
  left_motor.stop();
  right_motor.stop();
  left_pid.reset();
  right_pid.reset();
}

void applyVelocityCommand(const VelocityCommand &command) {
  const float half_track = robot.wheel_separation_m * 0.5f;
  target_left_rad_s =
      (command.linear_mps - command.angular_rps * half_track) / robot.wheel_radius_m;
  target_right_rad_s =
      (command.linear_mps + command.angular_rps * half_track) / robot.wheel_radius_m;

  const float max_rad_s = robot.max_rpm * TWO_PI / 60.0f;
  target_left_rad_s = constrain(target_left_rad_s, -max_rad_s, max_rad_s);
  target_right_rad_s = constrain(target_right_rad_s, -max_rad_s, max_rad_s);
  last_command_ms = millis();
}

void runControlLoop(uint32_t now_ms) {
  if (now_ms - last_control_ms < timing::CONTROL_PERIOD_MS) return;
  const float dt = (now_ms - last_control_ms) * 0.001f;
  last_control_ms = now_ms;

  const int32_t left_now = left_encoder.read();
  const int32_t right_now = right_encoder.read();
  const int32_t left_delta = left_now - previous_left_ticks;
  const int32_t right_delta = right_now - previous_right_ticks;
  previous_left_ticks = left_now;
  previous_right_ticks = right_now;

  const float tick_to_rad = TWO_PI / robot.counts_per_rev;
  const float measured_left_rad_s = left_delta * tick_to_rad / dt;
  const float measured_right_rad_s = right_delta * tick_to_rad / dt;

  if (emergencyStopActive() || now_ms - last_command_ms > robot.command_timeout_ms) {
    stopMotors();
    return;
  }

  left_motor.write(left_pid.update(target_left_rad_s, measured_left_rad_s, dt));
  right_motor.write(right_pid.update(target_right_rad_s, measured_right_rad_s, dt));
}

void updateImu(uint32_t now_ms) {
  if (!imu_available || now_ms - last_imu_ms < timing::IMU_PERIOD_MS) return;
  last_imu_ms = now_ms;
  imu.read(imu_sample);
}

void publishFeedback(uint32_t now_ms) {
  if (now_ms - last_feedback_ms < timing::FEEDBACK_PERIOD_MS) return;
  last_feedback_ms = now_ms;

  // Battery ADC is board-specific and remains disabled until its divider is known.
  constexpr float battery_voltage = 0.0f;
  protocol.publishFeedback(left_encoder.read(), right_encoder.read(), imu_sample,
                           battery_voltage, emergencyStopActive(), now_ms);
}

void setup() {
  pinMode(pins::ESTOP_IN, INPUT_PULLUP);
  pinMode(pins::STATUS_LED, OUTPUT);
  digitalWrite(pins::STATUS_LED, HIGH);

  left_motor.begin();
  right_motor.begin();
  left_encoder.begin(leftEncoderIsr);
  right_encoder.begin(rightEncoderIsr);

  RosSerial.begin(timing::BAUD);
  ImuWire.begin();
  ImuWire.setClock(400000);
  imu_available = imu.begin();

  stopMotors();
  const uint32_t now = millis();
  last_command_ms = now;
  last_control_ms = now;
  last_feedback_ms = now;
  last_imu_ms = now;
  digitalWrite(pins::STATUS_LED, imu_available ? LOW : HIGH);
}

void loop() {
  const uint32_t now_ms = millis();
  VelocityCommand command;
  if (protocol.poll(command)) applyVelocityCommand(command);
  updateImu(now_ms);
  runControlLoop(now_ms);
  publishFeedback(now_ms);
  digitalWrite(pins::STATUS_LED,
               (emergencyStopActive() || !imu_available) ? HIGH : LOW);
}
