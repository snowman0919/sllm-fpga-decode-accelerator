// Generator : SpinalHDL v1.14.2    git head : 78f29dc66110fc099a777992b6daa2f803ab445e
// Component : DotProductInt8_dim16

`timescale 1ns/1ps 
module DotProductInt8_dim16 (
  input  wire          io_start,
  input  wire [7:0]    io_query_0,
  input  wire [7:0]    io_query_1,
  input  wire [7:0]    io_query_2,
  input  wire [7:0]    io_query_3,
  input  wire [7:0]    io_query_4,
  input  wire [7:0]    io_query_5,
  input  wire [7:0]    io_query_6,
  input  wire [7:0]    io_query_7,
  input  wire [7:0]    io_query_8,
  input  wire [7:0]    io_query_9,
  input  wire [7:0]    io_query_10,
  input  wire [7:0]    io_query_11,
  input  wire [7:0]    io_query_12,
  input  wire [7:0]    io_query_13,
  input  wire [7:0]    io_query_14,
  input  wire [7:0]    io_query_15,
  input  wire [7:0]    io_key_0,
  input  wire [7:0]    io_key_1,
  input  wire [7:0]    io_key_2,
  input  wire [7:0]    io_key_3,
  input  wire [7:0]    io_key_4,
  input  wire [7:0]    io_key_5,
  input  wire [7:0]    io_key_6,
  input  wire [7:0]    io_key_7,
  input  wire [7:0]    io_key_8,
  input  wire [7:0]    io_key_9,
  input  wire [7:0]    io_key_10,
  input  wire [7:0]    io_key_11,
  input  wire [7:0]    io_key_12,
  input  wire [7:0]    io_key_13,
  input  wire [7:0]    io_key_14,
  input  wire [7:0]    io_key_15,
  output wire          io_busy,
  output wire          io_done,
  output wire [31:0]   io_score,
  input  wire          clk,
  input  wire          reset
);

  wire       [31:0]   _zz__zz_accReg;
  wire       [15:0]   _zz__zz_accReg_1;
  reg        [7:0]    _zz__zz_accReg_2;
  reg        [7:0]    _zz__zz_accReg_3;
  wire       [3:0]    lastIndex;
  reg                 busyReg;
  reg                 doneReg;
  reg        [3:0]    indexReg;
  reg        [31:0]   accReg;
  reg        [31:0]   scoreReg;
  wire                when_DotProductInt8_l40;
  wire       [31:0]   _zz_accReg;
  wire                when_DotProductInt8_l51;

  assign _zz__zz_accReg_1 = ($signed(_zz__zz_accReg_2) * $signed(_zz__zz_accReg_3));
  assign _zz__zz_accReg = {{16{_zz__zz_accReg_1[15]}}, _zz__zz_accReg_1};
  always @(*) begin
    case(indexReg)
      4'b0000 : begin
        _zz__zz_accReg_2 = io_query_0;
        _zz__zz_accReg_3 = io_key_0;
      end
      4'b0001 : begin
        _zz__zz_accReg_2 = io_query_1;
        _zz__zz_accReg_3 = io_key_1;
      end
      4'b0010 : begin
        _zz__zz_accReg_2 = io_query_2;
        _zz__zz_accReg_3 = io_key_2;
      end
      4'b0011 : begin
        _zz__zz_accReg_2 = io_query_3;
        _zz__zz_accReg_3 = io_key_3;
      end
      4'b0100 : begin
        _zz__zz_accReg_2 = io_query_4;
        _zz__zz_accReg_3 = io_key_4;
      end
      4'b0101 : begin
        _zz__zz_accReg_2 = io_query_5;
        _zz__zz_accReg_3 = io_key_5;
      end
      4'b0110 : begin
        _zz__zz_accReg_2 = io_query_6;
        _zz__zz_accReg_3 = io_key_6;
      end
      4'b0111 : begin
        _zz__zz_accReg_2 = io_query_7;
        _zz__zz_accReg_3 = io_key_7;
      end
      4'b1000 : begin
        _zz__zz_accReg_2 = io_query_8;
        _zz__zz_accReg_3 = io_key_8;
      end
      4'b1001 : begin
        _zz__zz_accReg_2 = io_query_9;
        _zz__zz_accReg_3 = io_key_9;
      end
      4'b1010 : begin
        _zz__zz_accReg_2 = io_query_10;
        _zz__zz_accReg_3 = io_key_10;
      end
      4'b1011 : begin
        _zz__zz_accReg_2 = io_query_11;
        _zz__zz_accReg_3 = io_key_11;
      end
      4'b1100 : begin
        _zz__zz_accReg_2 = io_query_12;
        _zz__zz_accReg_3 = io_key_12;
      end
      4'b1101 : begin
        _zz__zz_accReg_2 = io_query_13;
        _zz__zz_accReg_3 = io_key_13;
      end
      4'b1110 : begin
        _zz__zz_accReg_2 = io_query_14;
        _zz__zz_accReg_3 = io_key_14;
      end
      default : begin
        _zz__zz_accReg_2 = io_query_15;
        _zz__zz_accReg_3 = io_key_15;
      end
    endcase
  end

  assign lastIndex = 4'b1111;
  assign io_busy = busyReg;
  assign io_done = doneReg;
  assign io_score = scoreReg;
  assign when_DotProductInt8_l40 = (io_start && (! busyReg));
  assign _zz_accReg = ($signed(accReg) + $signed(_zz__zz_accReg));
  assign when_DotProductInt8_l51 = (indexReg == lastIndex);
  always @(posedge clk or posedge reset) begin
    if(reset) begin
      busyReg <= 1'b0;
      doneReg <= 1'b0;
      indexReg <= 4'b0000;
      accReg <= 32'h0;
      scoreReg <= 32'h0;
    end else begin
      doneReg <= 1'b0;
      if(when_DotProductInt8_l40) begin
        busyReg <= 1'b1;
        indexReg <= 4'b0000;
        accReg <= 32'h0;
        scoreReg <= 32'h0;
      end else begin
        if(busyReg) begin
          accReg <= _zz_accReg;
          if(when_DotProductInt8_l51) begin
            busyReg <= 1'b0;
            doneReg <= 1'b1;
            scoreReg <= _zz_accReg;
          end else begin
            indexReg <= (indexReg + 4'b0001);
          end
        end
      end
    end
  end


endmodule
