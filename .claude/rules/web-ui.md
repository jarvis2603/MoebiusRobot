# Robotics Web UI Rule

Preferred stack: React + Vite + Bootstrap, roslibjs/rosbridge; Node.js backend only when server-side capability is actually required.

Structure UI into components, hooks/context and ROS services/adapters. Do not put ROS subscriptions, navigation logic and all presentation into App.jsx.

Required robustness: WebSocket reconnect/backoff, subscription cleanup, connection/error states, responsive/touch UI and configurable topic/service names through environment/config.

For maps account for OccupancyGrid origin/resolution and coordinate transforms. Never assume LaserScan is already in map frame. Display global/local paths, footprint, robot pose and goal markers using verified frames.

Safety: Web UI is supervisory only. On loss of WebSocket, browser focus or manual-control release, publish zero manual velocity. Respect STOPPED/MANUAL/AUTO/FAULT/ESTOP states. Never let manual and Nav2 commands compete directly on final /cmd_vel.

Production: npm build, Nginx reverse proxy, WSS/HTTPS and authentication when outside a trusted robot LAN. Avoid exposing privileged system controls directly through rosbridge.