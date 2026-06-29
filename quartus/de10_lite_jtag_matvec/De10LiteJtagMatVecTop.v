`timescale 1ns/1ps

module De10LiteJtagMatVecTop (
  input  wire        CLOCK_50,
  input  wire [1:0]  KEY,
  input  wire [9:0]  SW,
  output wire [9:0]  LEDR,
  output wire [6:0]  HEX0,
  output wire [6:0]  HEX1,
  output wire [6:0]  HEX2,
  output wire [6:0]  HEX3,
  output wire [6:0]  HEX4,
  output wire [6:0]  HEX5
);

  wire [9:0] unused_sw = SW;
  wire unused_key1 = KEY[1];

  wire [7:0] hex0_full;
  wire [7:0] hex1_full;
  wire [7:0] hex2_full;
  wire [7:0] hex3_full;
  wire [7:0] hex4_full;
  wire [7:0] hex5_full;

  jtag_matvec_system system_inst (
    .CLOCK_50_clk(CLOCK_50),
    .KEY_reset_n(KEY[0]),
    .LEDR_export(LEDR),
    .HEX0_export(hex0_full),
    .HEX1_export(hex1_full),
    .HEX2_export(hex2_full),
    .HEX3_export(hex3_full),
    .HEX4_export(hex4_full),
    .HEX5_export(hex5_full)
  );

  assign HEX0 = hex0_full[6:0];
  assign HEX1 = hex1_full[6:0];
  assign HEX2 = hex2_full[6:0];
  assign HEX3 = hex3_full[6:0];
  assign HEX4 = hex4_full[6:0];
  assign HEX5 = hex5_full[6:0];

endmodule
