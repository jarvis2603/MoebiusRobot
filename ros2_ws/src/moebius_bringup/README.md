# Moebius Raspberry Pi Auto Start

This package starts the headless ROS 2 stack at boot and serves the React UI through Nginx.

## Install

Run as the normal Raspberry Pi user from the repository root:

```bash
bash ros2_ws/src/moebius_bringup/scripts/install_boot.sh
sudo reboot
```

After reboot open:

```text
http://moebius.local
```

The actual hostname is used, so check it with `hostname`.

## Configuration

```bash
sudo nano /etc/moebius/moebius.env
```

Important values:

```dotenv
SERIAL_PORT=/dev/ttyUSB0
USE_SLAM=false
USE_NAV2=false
USE_SIM_TIME=false
ROS_DOMAIN_ID=0
```

For mapping:

```dotenv
USE_SLAM=true
USE_NAV2=true
```

For an existing map/localization deployment, keep `USE_SLAM=false`, enable Nav2, and replace `NAV2_PARAMS` with the robot-specific Nav2 YAML. A map server and AMCL launch should be added once the final map path is known.

## Operations

```bash
sudo systemctl status moebius-robot --no-pager
sudo systemctl restart moebius-robot
sudo systemctl stop moebius-robot
sudo systemctl disable moebius-robot
journalctl -u moebius-robot -f
```

Check the web server:

```bash
systemctl status nginx --no-pager
curl http://localhost/healthz
```

Check rosbridge:

```bash
ss -lntp | grep 9090
```

## Update after pulling new code

```bash
cd ~/MoebiusRobot
source /opt/ros/jazzy/setup.bash
cd ros2_ws
colcon build --symlink-install
cd ../web_ui
npm install
npm run build
sudo rm -rf /var/www/moebius/*
sudo cp -a dist/. /var/www/moebius/
sudo systemctl restart moebius-robot nginx
```

## Safety

Boot always leaves motion under the robot supervisor, firmware watchdog, motor-enable logic, and physical E-stop. Do not use the browser or systemd as the primary safety mechanism.
