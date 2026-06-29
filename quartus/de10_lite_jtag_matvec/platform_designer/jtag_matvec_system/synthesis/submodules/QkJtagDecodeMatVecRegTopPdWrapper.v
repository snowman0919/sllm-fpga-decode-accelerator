`timescale 1ns/1ps

module QkJtagDecodeMatVecRegTopPdWrapper (
  input  wire          clk,
  input  wire          reset,
  input  wire [11:0]   avs_address,
  input  wire          avs_read,
  input  wire          avs_write,
  input  wire [3:0]    avs_byteenable,
  input  wire [31:0]   avs_writedata,
  output wire [31:0]   avs_readdata,
  output wire          avs_waitrequest,
  output wire          avs_readdatavalid,
  output wire [9:0]    LEDR,
  output wire [7:0]    HEX0,
  output wire [7:0]    HEX1,
  output wire [7:0]    HEX2,
  output wire [7:0]    HEX3,
  output wire [7:0]    HEX4,
  output wire [7:0]    HEX5
);

  wire unused_reset = reset;
  wire [3:0] unused_byteenable = avs_byteenable;

  JtagDecodeMatVecRegTop core (
    .CLOCK_50(clk),
    .avs_address(avs_address),
    .avs_read(avs_read),
    .avs_write(avs_write),
    .avs_writedata(avs_writedata),
    .avs_readdata(avs_readdata),
    .avs_waitrequest(avs_waitrequest),
    .avs_readdatavalid(avs_readdatavalid),
    .LEDR(LEDR),
    .HEX0(HEX0),
    .HEX1(HEX1),
    .HEX2(HEX2),
    .HEX3(HEX3),
    .HEX4(HEX4),
    .HEX5(HEX5)
  );

endmodule
