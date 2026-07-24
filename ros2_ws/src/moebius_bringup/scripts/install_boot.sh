#!/usr/bin/env bash
set -euo pipefail

if [[ ${EUID} -eq 0 ]]; then
  echo "Run this script as the normal robot user, not root." >&2
  exit 1
fi

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
ROBOT_USER="${SUDO_USER:-$USER}"
ROS_DISTRO="${ROS_DISTRO:-jazzy}"
ENV_DIR=/etc/moebius
ENV_FILE=${ENV_DIR}/moebius.env
WEB_ROOT=/var/www/moebius
SERVICE=/etc/systemd/system/moebius-robot.service
NGINX_SITE=/etc/nginx/sites-available/moebius

sudo apt update
sudo apt install -y \
  nginx avahi-daemon curl nodejs npm python3-rosdep python3-colcon-common-extensions \
  ros-${ROS_DISTRO}-rosbridge-server \
  ros-${ROS_DISTRO}-navigation2 \
  ros-${ROS_DISTRO}-nav2-bringup \
  ros-${ROS_DISTRO}-slam-toolbox \
  ros-${ROS_DISTRO}-robot-state-publisher \
  ros-${ROS_DISTRO}-xacro

sudo usermod -aG dialout,video,render,input "$ROBOT_USER"

source "/opt/ros/${ROS_DISTRO}/setup.bash"
cd "${REPO_DIR}/ros2_ws"
rosdep update
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install

cd "${REPO_DIR}/web_ui"
npm install
VITE_ROSBRIDGE_URL="ws://$(hostname).local/rosbridge" npm run build
sudo install -d -m 0755 "$WEB_ROOT"
sudo rm -rf "${WEB_ROOT:?}"/*
sudo cp -a dist/. "$WEB_ROOT/"

sudo install -d -m 0755 "$ENV_DIR" /var/log/moebius/ros
if [[ ! -f "$ENV_FILE" ]]; then
  sed \
    -e "s|MOEBIUS_USER=ubuntu|MOEBIUS_USER=${ROBOT_USER}|" \
    -e "s|MOEBIUS_REPO=/home/ubuntu/MoebiusRobot|MOEBIUS_REPO=${REPO_DIR}|" \
    -e "s|ROS_DISTRO=jazzy|ROS_DISTRO=${ROS_DISTRO}|" \
    -e "s|/home/ubuntu/MoebiusRobot|${REPO_DIR}|g" \
    "${REPO_DIR}/ros2_ws/src/moebius_bringup/config/moebius.env.example" | sudo tee "$ENV_FILE" >/dev/null
fi

sed \
  -e "s|__MOEBIUS_USER__|${ROBOT_USER}|g" \
  -e "s|__MOEBIUS_REPO__|${REPO_DIR}|g" \
  "${REPO_DIR}/ros2_ws/src/moebius_bringup/systemd/moebius-robot.service" | sudo tee "$SERVICE" >/dev/null

sudo cp "${REPO_DIR}/ros2_ws/src/moebius_bringup/nginx/moebius.conf" "$NGINX_SITE"
sudo ln -sfn "$NGINX_SITE" /etc/nginx/sites-enabled/moebius
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t

sudo systemctl daemon-reload
sudo systemctl enable nginx avahi-daemon moebius-robot.service
sudo systemctl restart nginx avahi-daemon
sudo systemctl restart moebius-robot.service

printf '\nInstalled successfully.\n'
printf 'Web UI: http://%s.local\n' "$(hostname)"
printf 'Edit configuration: sudo nano %s\n' "$ENV_FILE"
printf 'Robot status: systemctl status moebius-robot --no-pager\n'
printf 'Robot logs: journalctl -u moebius-robot -f\n'
printf '\nLog out and back in, or reboot, so new device groups apply.\n'
