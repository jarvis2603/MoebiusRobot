# KiCad / PCB Robotics Rule

Design from verified requirements and datasheets. Maintain a power budget and interface table before committing schematic topology.

Review: input protection, regulators, logic rails, motor/servo rails, grounding, decoupling, bulk capacitance, reverse polarity, surge/transient/ESD protection, level shifting, connector current/voltage ratings, test points and SWD/JTAG/UART access.

Separate high-current motor paths from sensitive analog/sensor paths. Size copper width/vias from expected continuous and transient current plus temperature rise; do not guess.

For MCU pin allocation, record every peripheral and alternate-function conflict. Reserve debug/programming access.

Before PCB completion run ERC and DRC and review placement/routing against return-current paths, thermal needs, EMI and manufacturability.

When changing a connector or pinout, flag required firmware, harness and documentation changes.