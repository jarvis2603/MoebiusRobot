#include <Arduino.h>
#include <math.h>

// MoebiusRobot STM32F103RCT6 firmware starter for ROS 2 Jazzy.
// IMPORTANT: verify every pin against the actual controller schematic.

namespace pins {
constexpr PinName ROS_RX = PA_10;   // USART1 RX
constexpr PinName ROS_TX = PA_9;    // USART1 TX
constexpr uint32_t LEFT_PWM = PA0;
constexpr uint32_t RIGHT_PWM = PA1;
constexpr uint32_t LEFT_DIR = PB0;
constexpr uint32_t RIGHT_DIR = PB1;
constexpr uint32_t LEFT_ENC_A = PB6;
constexpr uint32_t RIGHT_ENC_A = PB7;
constexpr uint32_t ESTOP_IN = PB8;
constexpr uint32_t STATUS_LED = PC13;
}  // namespace pins

HardwareSerial RosSerial(pins::ROS_RX, pins::ROS_TX);

namespace config {
constexpr uint32_t BAUD = 115200;
constexpr uint32_t CONTROL_PERIOD_MS = 10;
constexpr uint32_t FEEDBACK_PERIOD_MS = 20;
constexpr uint32_t COMMAND_TIMEOUT_MS = 300;
constexpr float WHEEL_RADIUS_M = 0.080f;       // Replace with measured value.
constexpr float WHEEL_SEPARATION_M = 0.360f;   // Replace with measured value.
constexpr float TICKS_PER_REV = 2048.0f;       // Include gearbox and quadrature factor.
constexpr float MAX_WHEEL_RAD_S = 20.0f;
constexpr int PWM_MAX = 255;
}  // namespace config

volatile int32_t left_ticks = 0;
volatile int32_t right_ticks = 0;

struct Pid {
  float kp{18.0f};
  float ki{4.0f};
  float kd{0.10f};
  float integral{0.0f};
  float previous_error{0.0f};

  float update(float target, float measured, float dt) {
    const float error = target - measured;
    integral = constrain(integral + error * dt, -50.0f, 50.0f);
    const float derivative = (dt > 0.0f) ? (error - previous_error) / dt : 0.0f;
    previous_error = error;
    return kp * error + ki * integral + kd * derivative;
  }

  void reset() {
    integral = 0.0f;
    previous_error = 0.0f;
  }
};

Pid left_pid;
Pid right_pid;
float target_left_rad_s = 0.0f;
float target_right_rad_s = 0.0f;
int32_t previous_left_ticks = 0;
int32_t previous_right_ticks = 0;
uint32_t last_command_ms = 0;
uint32_t last_control_ms = 0;
uint32_t last_feedback_ms = 0;
String rx_line;

void leftEncoderIsr() { ++left_ticks; }
void rightEncoderIsr() { ++right_ticks; }

void setMotor(uint32_t pwm_pin, uint32_t dir_pin, float command) {
  const bool forward = command >= 0.0f;
  const int pwm = constrain(static_cast<int>(fabsf(command)), 0, config::PWM_MAX);
  digitalWrite(dir_pin, forward ? HIGH : LOW);
  analogWrite(pwm_pin, pwm);
}

void stopMotors() {
  target_left_rad_s = 0.0f;
  target_right_rad_s = 0.0f;
  analogWrite(pins::LEFT_PWM, 0);
  analogWrite(pins::RIGHT_PWM, 0);
  left_pid.reset();
  right_pid.reset();
}

bool emergencyStopActive() {
  return digitalRead(pins::ESTOP_IN) == LOW;
}

void parseCommand(const String &line) {
  // Expected frame: CMD,<linear_mps>,<angular_rps>
  if (!line.startsWith("CMD,")) {
    return;
  }

  const int comma1 = line.indexOf(',');
  const int comma2 = line.indexOf(',', comma1 + 1);
  if (comma1 < 0 || comma2 < 0) {
    return;
  }

  const float linear = line.substring(comma1 + 1, comma2).toFloat();
  const float angular = line.substring(comma2 + 1).toFloat();
  if (!isfinite(linear) || !isfinite(angular)) {
    return;
  }

  const float half_track = config::WHEEL_SEPARATION_M * 0.5f;
  target_left_rad_s = (linear - angular * half_track) / config::WHEEL_RADIUS_M;
  target_right_rad_s = (linear + angular * half_track) / config::WHEEL_RADIUS_M;
  target_left_rad_s = constrain(target_left_rad_s, -config::MAX_WHEEL_RAD_S,
                                config::MAX_WHEEL_RAD_S);
  target_right_rad_s = constrain(target_right_rad_s, -config::MAX_WHEEL_RAD_S,
                                 config::MAX_WHEEL_RAD_S);
  last_command_ms = millis();
}

void readSerialCommands() {
  while (RosSerial.available() > 0) {
    const char c = static_cast<char>(RosSerial.read());
    if (c == '\n') {
      rx_line.trim();
      parseCommand(rx_line);
      rx_line = "";
    } else if (c != '\r' && rx_line.length() < 96) {
      rx_line += c;
    }
  }
}

void runControlLoop(uint32_t now_ms) {
  if (now_ms - last_control_ms < config::CONTROL_PERIOD_MS) {
    return;
  }

  const float dt = (now_ms - last_control_ms) * 0.001f;
  last_control_ms = now_ms;

  noInterrupts();
  const int32_t left_now = left_ticks;
  const int32_t right_now = right_ticks;
  interrupts();

  const int32_t left_delta = left_now - previous_left_ticks;
  const int32_t right_delta = right_now - previous_right_ticks;
  previous_left_ticks = left_now;
  previous_right_ticks = right_now;

  const float tick_to_rad = 2.0f * PI / config::TICKS_PER_REV;
  const float measured_left = left_delta * tick_to_rad / dt;
  const float measured_right = right_delta * tick_to_rad / dt;

  const bool timed_out = now_ms - last_command_ms > config::COMMAND_TIMEOUT_MS;
  if (timed_out || emergencyStopActive()) {
    stopMotors();
    return;
  }

  setMotor(pins::LEFT_PWM, pins::LEFT_DIR,
           left_pid.update(target_left_rad_s, measured_left, dt));
  setMotor(pins::RIGHT_PWM, pins::RIGHT_DIR,
           right_pid.update(target_right_rad_s, measured_right, dt));
}

void publishFeedback(uint32_t now_ms) {
  if (now_ms - last_feedback_ms < config::FEEDBACK_PERIOD_MS) {
    return;
  }
  last_feedback_ms = now_ms;

  noInterrupts();
  const int32_t left_now = left_ticks;
  const int32_t right_now = right_ticks;
  interrupts();

  // Compatible with the ROS 2 starter driver:
  // FB,<left_ticks>,<right_ticks>,<gyro_z_rad_s>,<battery_voltage>
  // IMU and battery acquisition are placeholders until the actual hardware is known.
  const float gyro_z = 0.0f;
  const float battery_voltage = 0.0f;
  RosSerial.print("FB,");
  RosSerial.print(left_now);
  RosSerial.print(',');
  RosSerial.print(right_now);
  RosSerial.print(',');
  RosSerial.print(gyro_z, 6);
  RosSerial.print(',');
  RosSerial.println(battery_voltage, 3);
}

void setup() {
  pinMode(pins::LEFT_PWM, OUTPUT);
  pinMode(pins::RIGHT_PWM, OUTPUT);
  pinMode(pins::LEFT_DIR, OUTPUT);
  pinMode(pins::RIGHT_DIR, OUTPUT);
  pinMode(pins::LEFT_ENC_A, INPUT_PULLUP);
  pinMode(pins::RIGHT_ENC_A, INPUT_PULLUP);
  pinMode(pins::ESTOP_IN, INPUT_PULLUP);
  pinMode(pins::STATUS_LED, OUTPUT);

  attachInterrupt(digitalPinToInterrupt(pins::LEFT_ENC_A), leftEncoderIsr, RISING);
  attachInterrupt(digitalPinToInterrupt(pins::RIGHT_ENC_A), rightEncoderIsr, RISING);

  RosSerial.begin(config::BAUD);
  stopMotors();
  last_command_ms = millis();
  last_control_ms = millis();
  digitalWrite(pins::STATUS_LED, LOW);
}

void loop() {
  const uint32_t now_ms = millis();
  readSerialCommands();
  runControlLoop(now_ms);
  publishFeedback(now_ms);
  digitalWrite(pins::STATUS_LED, emergencyStopActive() ? HIGH : LOW);
}
