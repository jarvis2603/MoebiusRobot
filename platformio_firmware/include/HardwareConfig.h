#pragma once

#include <Arduino.h>
#include "generated/RobotSpecs.h"

namespace hw {

// Board: Moebius Mecanum TB6612, STM32F103RCT6.
// Pin assignments are derived from the uploaded board schematic.

constexpr uint32_t ROS_UART_TX = PA9;
constexpr uint32_t ROS_UART_RX = PA10;
constexpr uint32_t ROS_UART_BAUD = robot_specs::ROS_UART_BAUD;

constexpr uint32_t I2C2_SCL = PB10;
constexpr uint32_t I2C2_SDA = PB11;
constexpr uint8_t MPU6050_ADDRESS = 0x68;
constexpr uint8_t HMC5883L_ADDRESS = 0x1E;
constexpr uint8_t OLED_ADDRESS = 0x3C;

// TB6612 U6: motors A/B.
constexpr uint32_t MOTOR_A_IN1 = PC5;
constexpr uint32_t MOTOR_A_IN2 = PC4;
constexpr uint32_t MOTOR_A_PWM = PC7;
constexpr uint32_t MOTOR_B_IN1 = PB0;
constexpr uint32_t MOTOR_B_IN2 = PB1;
constexpr uint32_t MOTOR_B_PWM = PC6;

// TB6612 U7: motors C/D.
constexpr uint32_t MOTOR_C_IN1 = PD2;
constexpr uint32_t MOTOR_C_IN2 = PC12;
constexpr uint32_t MOTOR_C_PWM = PC9;
constexpr uint32_t MOTOR_D_IN1 = PB4;
constexpr uint32_t MOTOR_D_IN2 = PB5;
constexpr uint32_t MOTOR_D_PWM = PC8;

// Quadrature encoder inputs from MA/MB/MC/MD headers.
constexpr uint32_t ENCODER_A_CH_A = PA15;
constexpr uint32_t ENCODER_A_CH_B = PB3;
constexpr uint32_t ENCODER_B_CH_A = PA6;
constexpr uint32_t ENCODER_B_CH_B = PA7;
constexpr uint32_t ENCODER_C_CH_A = PB6;
constexpr uint32_t ENCODER_C_CH_B = PB7;
constexpr uint32_t ENCODER_D_CH_A = PA0;
constexpr uint32_t ENCODER_D_CH_B = PA1;

constexpr uint32_t BATTERY_ADC = PA5;
constexpr float BATTERY_R_TOP_OHM = 10000.0f;
constexpr float BATTERY_R_BOTTOM_OHM = 1000.0f;
constexpr float ADC_REFERENCE_V = 3.3f;
constexpr float BATTERY_CALIBRATION = 1.0f;

constexpr uint32_t STATUS_LED = PC13;
constexpr uint32_t USER_KEY = PC0;

// Generated mechanical, drivetrain and control values.
constexpr float WHEEL_RADIUS_M = robot_specs::WHEEL_RADIUS_M;
constexpr float WHEELBASE_X_M = robot_specs::HALF_WHEELBASE_M;
constexpr float WHEELBASE_Y_M = robot_specs::HALF_TRACK_WIDTH_M;
constexpr float COUNTS_PER_REV = static_cast<float>(robot_specs::COUNTS_PER_WHEEL_REV);
constexpr float MAX_RPM = robot_specs::MOTOR_RATED_OUTPUT_RPM;
constexpr float MAX_LINEAR_VELOCITY_MPS = robot_specs::MAX_LINEAR_VELOCITY_MPS;
constexpr float MAX_LATERAL_VELOCITY_MPS = robot_specs::MAX_LATERAL_VELOCITY_MPS;
constexpr float MAX_ANGULAR_VELOCITY_RPS = robot_specs::MAX_ANGULAR_VELOCITY_RPS;

constexpr float PID_KP = robot_specs::PID_KP;
constexpr float PID_KI = robot_specs::PID_KI;
constexpr float PID_KD = robot_specs::PID_KD;

constexpr uint32_t CONTROL_PERIOD_US = robot_specs::CONTROL_PERIOD_US;
constexpr uint32_t FEEDBACK_PERIOD_MS = robot_specs::FEEDBACK_PERIOD_MS;
constexpr uint32_t IMU_PERIOD_MS = 20;
constexpr uint32_t OLED_PERIOD_MS = 500;
constexpr uint32_t COMMAND_TIMEOUT_MS = robot_specs::COMMAND_TIMEOUT_MS;

constexpr float BATTERY_EMPTY_V = robot_specs::BATTERY_EMPTY_V;
constexpr float BATTERY_FULL_V = robot_specs::BATTERY_FULL_V;
constexpr float BATTERY_CRITICAL_V = robot_specs::BATTERY_CRITICAL_V;

}  // namespace hw
