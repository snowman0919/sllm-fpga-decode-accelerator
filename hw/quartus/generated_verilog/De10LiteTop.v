// Generator : SpinalHDL v1.14.2    git head : 78f29dc66110fc099a777992b6daa2f803ab445e
// Component : De10LiteTop

`timescale 1ns/1ps 
module De10LiteTop (
  input  wire          CLOCK_50,
  input  wire [9:0]    SW,
  input  wire [1:0]    KEY,
  output reg  [9:0]    LEDR,
  output wire [6:0]    HEX0,
  output wire [6:0]    HEX1,
  output wire [6:0]    HEX2,
  output wire [6:0]    HEX3,
  output wire [6:0]    HEX4,
  output wire [6:0]    HEX5
);

  wire                area_dot_io_start;
  wire       [3:0]    area_hex0_io_nibble;
  wire       [3:0]    area_hex1_io_nibble;
  wire       [3:0]    area_hex2_io_nibble;
  wire       [3:0]    area_hex3_io_nibble;
  wire       [3:0]    area_hex4_io_nibble;
  wire                area_dot_io_busy;
  wire                area_dot_io_done;
  wire       [31:0]   area_dot_io_score;
  wire       [6:0]    area_hex0_io_segments;
  wire       [6:0]    area_hex1_io_segments;
  wire       [6:0]    area_hex2_io_segments;
  wire       [6:0]    area_hex3_io_segments;
  wire       [6:0]    area_hex4_io_segments;
  wire       [6:0]    area_hex5_io_segments;
  wire       [15:0]   _zz_io_nibble;
  reg                 area_startPrev;
  reg        [15:0]   area_cycleCounter;
  wire                when_De10LiteTop_l45;
  wire       [31:0]   area_scoreBits;
  reg        [3:0]    area_statusNibble;

  assign _zz_io_nibble = area_cycleCounter;
  DotProductInt8 area_dot (
    .io_start    (area_dot_io_start      ), //i
    .io_query_0  (8'hf8                  ), //i
    .io_query_1  (8'hf9                  ), //i
    .io_query_2  (8'hfa                  ), //i
    .io_query_3  (8'hfb                  ), //i
    .io_query_4  (8'hfc                  ), //i
    .io_query_5  (8'hfd                  ), //i
    .io_query_6  (8'hfe                  ), //i
    .io_query_7  (8'hff                  ), //i
    .io_query_8  (8'h01                  ), //i
    .io_query_9  (8'h02                  ), //i
    .io_query_10 (8'h03                  ), //i
    .io_query_11 (8'h04                  ), //i
    .io_query_12 (8'h05                  ), //i
    .io_query_13 (8'h06                  ), //i
    .io_query_14 (8'h07                  ), //i
    .io_query_15 (8'h08                  ), //i
    .io_key_0    (8'h03                  ), //i
    .io_key_1    (8'hff                  ), //i
    .io_key_2    (8'h04                  ), //i
    .io_key_3    (8'hfe                  ), //i
    .io_key_4    (8'h05                  ), //i
    .io_key_5    (8'hfd                  ), //i
    .io_key_6    (8'h06                  ), //i
    .io_key_7    (8'hfc                  ), //i
    .io_key_8    (8'h02                  ), //i
    .io_key_9    (8'hfb                  ), //i
    .io_key_10   (8'h01                  ), //i
    .io_key_11   (8'hfa                  ), //i
    .io_key_12   (8'h0                   ), //i
    .io_key_13   (8'h07                  ), //i
    .io_key_14   (8'hf9                  ), //i
    .io_key_15   (8'h08                  ), //i
    .io_busy     (area_dot_io_busy       ), //o
    .io_done     (area_dot_io_done       ), //o
    .io_score    (area_dot_io_score[31:0]), //o
    .CLOCK_50    (CLOCK_50               )  //i
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
    .io_nibble   (area_statusNibble[3:0]    ), //i
    .io_segments (area_hex5_io_segments[6:0])  //o
  );
  initial begin
    area_startPrev = 1'b0;
    area_cycleCounter = 16'h0;
  end

  assign area_dot_io_start = (SW[0] && (! area_startPrev));
  assign when_De10LiteTop_l45 = (area_dot_io_busy && (area_cycleCounter != 16'hffff));
  assign area_scoreBits = area_dot_io_score;
  always @(*) begin
    area_statusNibble = 4'b0000;
    area_statusNibble[0] = area_dot_io_busy;
    area_statusNibble[1] = area_dot_io_done;
    area_statusNibble[2] = SW[0];
    area_statusNibble[3] = KEY[0];
  end

  assign area_hex0_io_nibble = area_scoreBits[3 : 0];
  assign area_hex1_io_nibble = area_scoreBits[7 : 4];
  assign area_hex2_io_nibble = area_scoreBits[11 : 8];
  assign area_hex3_io_nibble = area_scoreBits[15 : 12];
  assign area_hex4_io_nibble = _zz_io_nibble[3 : 0];
  assign HEX0 = area_hex0_io_segments;
  assign HEX1 = area_hex1_io_segments;
  assign HEX2 = area_hex2_io_segments;
  assign HEX3 = area_hex3_io_segments;
  assign HEX4 = area_hex4_io_segments;
  assign HEX5 = area_hex5_io_segments;
  always @(*) begin
    LEDR = 10'h0;
    LEDR[0] = area_dot_io_busy;
    LEDR[1] = area_dot_io_done;
    LEDR[2] = SW[0];
    LEDR[3] = KEY[0];
    LEDR[9 : 4] = area_scoreBits[5 : 0];
  end

  always @(posedge CLOCK_50) begin
    area_startPrev <= SW[0];
    if(when_De10LiteTop_l45) begin
      area_cycleCounter <= (area_cycleCounter + 16'h0001);
    end else begin
      if(area_dot_io_done) begin
        area_cycleCounter <= 16'h0;
      end
    end
  end


endmodule
