package require -exact qsys 13.0

set system_name jtag_matvec_system
set system_path ${system_name}.qsys

create_system $system_name
set_project_property DEVICE_FAMILY "MAX 10"
set_project_property DEVICE 10M50DAF484C7G
set_project_property HIDE_FROM_IP_CATALOG false

add_instance clk_0 clock_source
set_instance_parameter_value clk_0 clockFrequency 50000000
set_instance_parameter_value clk_0 clockFrequencyKnown true
set_instance_parameter_value clk_0 resetSynchronousEdges NONE

add_instance jtag_master altera_jtag_avalon_master
set_instance_parameter_value jtag_master USE_PLI 0
set_instance_parameter_value jtag_master FAST_VER 0

add_instance matvec qk_jtag_decode_matvec_reg_top

add_connection clk_0.clk jtag_master.clk clock
add_connection clk_0.clk_reset jtag_master.clk_reset reset
add_connection clk_0.clk matvec.clock clock
add_connection clk_0.clk_reset matvec.reset reset

add_connection jtag_master.master matvec.avs avalon
set_connection_parameter_value jtag_master.master/matvec.avs baseAddress 0x00000000

add_interface CLOCK_50 clock sink
set_interface_property CLOCK_50 EXPORT_OF clk_0.clk_in
add_interface KEY reset sink
set_interface_property KEY EXPORT_OF clk_0.clk_in_reset
add_interface LEDR conduit end
set_interface_property LEDR EXPORT_OF matvec.leds
add_interface HEX0 conduit end
set_interface_property HEX0 EXPORT_OF matvec.hex0
add_interface HEX1 conduit end
set_interface_property HEX1 EXPORT_OF matvec.hex1
add_interface HEX2 conduit end
set_interface_property HEX2 EXPORT_OF matvec.hex2
add_interface HEX3 conduit end
set_interface_property HEX3 EXPORT_OF matvec.hex3
add_interface HEX4 conduit end
set_interface_property HEX4 EXPORT_OF matvec.hex4
add_interface HEX5 conduit end
set_interface_property HEX5 EXPORT_OF matvec.hex5

save_system $system_path
puts "Generated $system_path"
