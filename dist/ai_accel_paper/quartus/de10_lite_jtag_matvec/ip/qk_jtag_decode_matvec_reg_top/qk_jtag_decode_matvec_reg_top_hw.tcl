package require -exact qsys 13.0

set_module_property NAME qk_jtag_decode_matvec_reg_top
set_module_property VERSION 0.1
set_module_property GROUP "Research/AI Accel"
set_module_property DISPLAY_NAME "QK JTAG Decode MatVec Register Top"
set_module_property DESCRIPTION "SpinalHDL-generated DecodeMatVecInt8 register bank exposed as an Avalon-MM slave."
set_module_property AUTHOR "ai_accel"
set_module_property INSTANTIATE_IN_SYSTEM_MODULE true
set_module_property EDITABLE false
set_module_property ANALYZE_HDL false

add_fileset QUARTUS_SYNTH QUARTUS_SYNTH "" ""
set_fileset_property QUARTUS_SYNTH TOP_LEVEL QkJtagDecodeMatVecRegTopPdWrapper
add_fileset_file DecodeMatVecInt8_i16_o4.v VERILOG PATH ../../generated_verilog/DecodeMatVecInt8_i16_o4.v
add_fileset_file DecodeMatVecRegBank.v VERILOG PATH ../../generated_verilog/DecodeMatVecRegBank.v
add_fileset_file HexDisplay.v VERILOG PATH ../../generated_verilog/HexDisplay.v
add_fileset_file JtagDecodeMatVecRegTop.v VERILOG PATH ../../generated_verilog/JtagDecodeMatVecRegTop.v
add_fileset_file QkJtagDecodeMatVecRegTopPdWrapper.v VERILOG PATH QkJtagDecodeMatVecRegTopPdWrapper.v TOP_LEVEL_FILE

add_fileset SIM_VERILOG SIM_VERILOG "" ""
set_fileset_property SIM_VERILOG TOP_LEVEL QkJtagDecodeMatVecRegTopPdWrapper
add_fileset_file DecodeMatVecInt8_i16_o4.v VERILOG PATH ../../generated_verilog/DecodeMatVecInt8_i16_o4.v
add_fileset_file DecodeMatVecRegBank.v VERILOG PATH ../../generated_verilog/DecodeMatVecRegBank.v
add_fileset_file HexDisplay.v VERILOG PATH ../../generated_verilog/HexDisplay.v
add_fileset_file JtagDecodeMatVecRegTop.v VERILOG PATH ../../generated_verilog/JtagDecodeMatVecRegTop.v
add_fileset_file QkJtagDecodeMatVecRegTopPdWrapper.v VERILOG PATH QkJtagDecodeMatVecRegTopPdWrapper.v TOP_LEVEL_FILE

add_interface clock clock end
set_interface_property clock ENABLED true
add_interface_port clock clk clk Input 1

add_interface reset reset end
set_interface_property reset associatedClock clock
set_interface_property reset synchronousEdges DEASSERT
add_interface_port reset reset reset Input 1

add_interface avs avalon end
set_interface_property avs associatedClock clock
set_interface_property avs associatedReset reset
set_interface_property avs ENABLED true
set_interface_property avs addressUnits SYMBOLS
set_interface_property avs addressAlignment DYNAMIC
set_interface_property avs maximumPendingReadTransactions 1
set_interface_property avs readLatency 0
set_interface_property avs setupTime 0
set_interface_property avs readWaitTime 0
set_interface_property avs writeWaitTime 0
add_interface_port avs avs_address address Input 12
add_interface_port avs avs_read read Input 1
add_interface_port avs avs_write write Input 1
add_interface_port avs avs_byteenable byteenable Input 4
add_interface_port avs avs_writedata writedata Input 32
add_interface_port avs avs_readdata readdata Output 32
add_interface_port avs avs_waitrequest waitrequest Output 1
add_interface_port avs avs_readdatavalid readdatavalid Output 1

add_interface leds conduit end
set_interface_property leds ENABLED true
add_interface_port leds LEDR export Output 10

add_interface hex0 conduit end
set_interface_property hex0 ENABLED true
add_interface_port hex0 HEX0 export Output 8

add_interface hex1 conduit end
set_interface_property hex1 ENABLED true
add_interface_port hex1 HEX1 export Output 8

add_interface hex2 conduit end
set_interface_property hex2 ENABLED true
add_interface_port hex2 HEX2 export Output 8

add_interface hex3 conduit end
set_interface_property hex3 ENABLED true
add_interface_port hex3 HEX3 export Output 8

add_interface hex4 conduit end
set_interface_property hex4 ENABLED true
add_interface_port hex4 HEX4 export Output 8

add_interface hex5 conduit end
set_interface_property hex5 ENABLED true
add_interface_port hex5 HEX5 export Output 8
