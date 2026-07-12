#pragma once

#include <Arduino.h>

// Verify these assignments against the actual Moebius controller schematic.
namespace pins {
constexpr PinName ROS_RX = PA_10;
constexpr PinName ROS_TX = PA_9;
constexpr uint32_t LEFT_PWM = PA0;
constexpr uint32_t RIGHT_PWM = PA1;
constexpr uint32_t LEFT_DIR = PB0;
constexpr uint32_t RIGHT_DIR = PB1;
constexpr uint32_t LEFT_ENC_A = PB6;
constexpr uint32_t RIGHT_ENC_A = PB7;
constexpr uint32_t ESTOP_IN = PB8;
constexpr uint32_t STATUS_LED = PC13;
}  // namespace pins
