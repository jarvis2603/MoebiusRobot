#pragma once

#include <Arduino.h>
#include <math.h>

struct ChassisVelocity {
  float vx{0.0f};
  float vy{0.0f};
  float wz{0.0f};
};

struct WheelVelocity {
  float front_left{0.0f};
  float front_right{0.0f};
  float rear_left{0.0f};
  float rear_right{0.0f};
};

class MecanumKinematics {
 public:
  MecanumKinematics(float wheel_radius, float half_length, float half_width)
      : r_(wheel_radius), lever_(half_length + half_width) {}

  WheelVelocity inverse(const ChassisVelocity &cmd) const {
    WheelVelocity out;
    out.front_left = (cmd.vx - cmd.vy - lever_ * cmd.wz) / r_;
    out.front_right = (cmd.vx + cmd.vy + lever_ * cmd.wz) / r_;
    out.rear_left = (cmd.vx + cmd.vy - lever_ * cmd.wz) / r_;
    out.rear_right = (cmd.vx - cmd.vy + lever_ * cmd.wz) / r_;
    return out;
  }

  ChassisVelocity forward(const WheelVelocity &wheel) const {
    ChassisVelocity out;
    out.vx = r_ * 0.25f * (wheel.front_left + wheel.front_right +
                           wheel.rear_left + wheel.rear_right);
    out.vy = r_ * 0.25f * (-wheel.front_left + wheel.front_right +
                           wheel.rear_left - wheel.rear_right);
    out.wz = r_ / (4.0f * lever_) * (-wheel.front_left + wheel.front_right -
                                      wheel.rear_left + wheel.rear_right);
    return out;
  }

  static void limit(WheelVelocity &wheel, float max_rad_s) {
    float peak = fabsf(wheel.front_left);
    peak = max(peak, fabsf(wheel.front_right));
    peak = max(peak, fabsf(wheel.rear_left));
    peak = max(peak, fabsf(wheel.rear_right));
    if (peak <= max_rad_s || peak <= 0.0f) return;
    const float scale = max_rad_s / peak;
    wheel.front_left *= scale;
    wheel.front_right *= scale;
    wheel.rear_left *= scale;
    wheel.rear_right *= scale;
  }

 private:
  float r_;
  float lever_;
};
