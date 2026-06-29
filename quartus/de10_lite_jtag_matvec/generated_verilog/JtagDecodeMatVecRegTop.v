// Generator : SpinalHDL v1.14.2    git head : 78f29dc66110fc099a777992b6daa2f803ab445e
// Component : JtagDecodeMatVecRegTop
// Git hash  : 1ae805c1d4479fef208c5cec7262211e4307cbc4

`timescale 1ns/1ps
module JtagDecodeMatVecRegTop (
  input  wire          CLOCK_50,
  input  wire [11:0]   avs_address,
  input  wire          avs_read,
  input  wire          avs_write,
  input  wire [31:0]   avs_writedata,
  output wire [31:0]   avs_readdata,
  output wire          avs_waitrequest,
  output wire          avs_readdatavalid,
  output reg  [9:0]    LEDR,
  output wire [6:0]    HEX0,
  output wire [6:0]    HEX1,
  output wire [6:0]    HEX2,
  output wire [6:0]    HEX3,
  output wire [6:0]    HEX4,
  output wire [6:0]    HEX5
);

  wire       [3:0]    area_hex0_io_nibble;
  wire       [3:0]    area_hex1_io_nibble;
  wire       [3:0]    area_hex2_io_nibble;
  wire       [3:0]    area_hex3_io_nibble;
  wire       [3:0]    area_hex4_io_nibble;
  reg        [3:0]    area_hex5_io_nibble;
  wire       [31:0]   area_regBank_io_readdata;
  wire                area_regBank_io_waitrequest;
  wire                area_regBank_io_readdatavalid;
  wire       [7:0]    area_regBank_io_debugStatus;
  wire       [7:0]    area_regBank_io_debugSeq;
  wire       [6:0]    area_hex0_io_segments;
  wire       [6:0]    area_hex1_io_segments;
  wire       [6:0]    area_hex2_io_segments;
  wire       [6:0]    area_hex3_io_segments;
  wire       [6:0]    area_hex4_io_segments;
  wire       [6:0]    area_hex5_io_segments;

  DecodeMatVecRegBank area_regBank (
    .io_address       (avs_address[11:0]               ), //i
    .io_read          (avs_read                        ), //i
    .io_write         (avs_write                       ), //i
    .io_writedata     (avs_writedata[31:0]             ), //i
    .io_readdata      (area_regBank_io_readdata[31:0]  ), //o
    .io_waitrequest   (area_regBank_io_waitrequest     ), //o
    .io_readdatavalid (area_regBank_io_readdatavalid   ), //o
    .io_debugStatus   (area_regBank_io_debugStatus[7:0]), //o
    .io_debugSeq      (area_regBank_io_debugSeq[7:0]   ), //o
    .CLOCK_50         (CLOCK_50                        )  //i
  );
  HexDisplay area_hex0 (
    .io_nibble   (area_hex0_io_nibble[3:0]  ), //i
    .io_segments (area_hex0_io_segments[6:0])  //o
  );
  HexDisplay area_hex1 (
    .io_nibble   (area_hex1_io_nibble[3:0]  ), //i
    .io_segments (area_hex1_io_segments[6:0])  //o
  );
  HexDisplay area_hex2 (
    .io_nibble   (area_hex2_io_nibble[3:0]  ), //i
    .io_segments (area_hex2_io_segments[6:0])  //o
  );
  HexDisplay area_hex3 (
    .io_nibble   (area_hex3_io_nibble[3:0]  ), //i
    .io_segments (area_hex3_io_segments[6:0])  //o
  );
  HexDisplay area_hex4 (
    .io_nibble   (area_hex4_io_nibble[3:0]  ), //i
    .io_segments (area_hex4_io_segments[6:0])  //o
  );
  HexDisplay area_hex5 (
    .io_nibble   (area_hex5_io_nibble[3:0]  ), //i
    .io_segments (area_hex5_io_segments[6:0])  //o
  );
  assign avs_readdata = area_regBank_io_readdata;
  assign avs_waitrequest = area_regBank_io_waitrequest;
  assign avs_readdatavalid = area_regBank_io_readdatavalid;
  assign area_hex0_io_nibble = area_regBank_io_debugStatus[3 : 0];
  assign area_hex1_io_nibble = area_regBank_io_debugStatus[7 : 4];
  assign area_hex2_io_nibble = area_regBank_io_debugSeq[3 : 0];
  assign area_hex3_io_nibble = area_regBank_io_debugSeq[7 : 4];
  assign area_hex4_io_nibble = avs_address[5 : 2];
  always @(*) begin
    area_hex5_io_nibble = 4'b0000;
    area_hex5_io_nibble[0] = avs_read;
    area_hex5_io_nibble[1] = avs_write;
    area_hex5_io_nibble[2] = avs_waitrequest;
    area_hex5_io_nibble[3] = avs_readdatavalid;
  end

  assign HEX0 = area_hex0_io_segments;
  assign HEX1 = area_hex1_io_segments;
  assign HEX2 = area_hex2_io_segments;
  assign HEX3 = area_hex3_io_segments;
  assign HEX4 = area_hex4_io_segments;
  assign HEX5 = area_hex5_io_segments;
  always @(*) begin
    LEDR = 10'h0;
    LEDR[7 : 0] = area_regBank_io_debugStatus;
    LEDR[8] = avs_read;
    LEDR[9] = avs_write;
  end


endmodule
