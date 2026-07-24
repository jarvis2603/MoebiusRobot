#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${MOEBIUS_ENV_FILE:-/etc/moebius/moebius.env}"
if [[ ! -r "$ENV_FILE" ]]; then
  echo "Missing environment file: $ENV_FILE" >&2
  exit 1
fi
# shellcheck disable=SC1090
source "$ENV_FILE"

: "${MOEBIUS_REPO:?MOEBIUS_REPO is required}"
: "${ROS_DISTRO:=jazzy}"
: "${SERIAL_PORT:=/dev/ttyUSB0}"
: "${USE_SLAM:=false}"
: "${USE_NAV2:=false}"
: "${USE_SIM_TIME:=false}"
: "${ROS_DOMAIN_ID:=0}"
: "${ROS_LOG_DIR:=/var/log/moebius/ros}"

export ROS_DOMAIN_ID ROS_LOG_DIR
if [[ -n "${RMW_IMPLEMENTATION:-}" ]]; then export RMW_IMPLEMENTATION; fi

source "/opt/ros/${ROS_DISTRO}/setup.bash"
source "${MOEBIUS_REPO}/ros2_ws/install/setup.bash"

ARGS=(
  "serial_port:=${SERIAL_PORT}"
  "use_slam:=${USE_SLAM}"
  "use_nav2:=${USE_NAV2}"
  "use_sim_time:=${USE_SIM_TIME}"
)
if [[ -n "${NAV2_PARAMS:-}" ]]; then
  ARGS+=("nav2_params:=${NAV2_PARAMS}")
fi

exec ros2 launch moebius_bringup robot.launch.py "${ARGS[@]}"
