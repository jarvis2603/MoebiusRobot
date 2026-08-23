# Coding / Repository Standard

Inspect before editing. Preserve established package layout and naming unless a migration explicitly justifies change.

Prefer small cohesive modules, explicit interfaces, configuration files and generated configuration from a single source of truth. Avoid magic numbers and duplicated mechanical/electrical constants.

C++: RAII, fixed-width types where protocol/hardware width matters, explicit units, bounded buffers in MCU code and no dynamic allocation in critical loops unless justified.

Python: type hints for public interfaces, clear node ownership, parameters rather than embedded deployment values, robust exception/log handling.

React/JS: components + hooks/services, cleanup timers/subscriptions, avoid global mutable ROS objects, environment-driven endpoints.

Every significant change should include relevant documentation/config updates. Build/lint/test the affected layer when tools are available. Report what was tested versus what still requires hardware verification.