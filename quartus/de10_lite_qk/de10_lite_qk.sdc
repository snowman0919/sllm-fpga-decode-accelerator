# 50 MHz board clock constraint for the DE10-Lite top-level wrapper.
# Pin mapping still comes from a verified DE10-Lite QSF import.
create_clock -name CLOCK_50 -period 20.000 [get_ports {CLOCK_50}]
