# Robot Safety Rule

Default startup state is STOPPED/DISARMED. Motor enable requires explicit valid command and healthy interlocks.

Physical E-stop and MCU watchdog are authoritative. Linux, ROS 2, Node.js and browser code are not substitutes for hardware/firmware safety.

Any command timeout, invalid control frame, critical battery condition or critical controller fault must result in deterministic safe motor output.

Mode rules:
- STOPPED: no teleop, no Nav2 motion
- MANUAL: manual source allowed, active autonomous goal cancelled
- AUTO: manual source blocked, autonomous navigation allowed
- FAULT: motion disabled until fault is resolved/reset
- ESTOP: motor output disabled; software cannot override a physically active E-stop

Use velocity/acceleration limits and arbitration. Never bypass an interlock merely to get a test moving. Bench tests involving actuators should begin unloaded/lifted where mechanically appropriate and at conservative limits.