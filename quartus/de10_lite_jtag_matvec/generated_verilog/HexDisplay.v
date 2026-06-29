// Generator : SpinalHDL v1.14.2    git head : 78f29dc66110fc099a777992b6daa2f803ab445e
// Component : HexDisplay
// Git hash  : 1ae805c1d4479fef208c5cec7262211e4307cbc4

`timescale 1ns/1ps
module HexDisplay (
  input  wire [3:0]    io_nibble,
  output reg  [6:0]    io_segments
);


  always @(*) begin
    io_segments = 7'h7f;
    case(io_nibble)
      4'b0000 : begin
        io_segments = 7'h40;
      end
      4'b0001 : begin
        io_segments = 7'h79;
      end
      4'b0010 : begin
        io_segments = 7'h24;
      end
      4'b0011 : begin
        io_segments = 7'h30;
      end
      4'b0100 : begin
        io_segments = 7'h19;
      end
      4'b0101 : begin
        io_segments = 7'h12;
      end
      4'b0110 : begin
        io_segments = 7'h02;
      end
      4'b0111 : begin
        io_segments = 7'h78;
      end
      4'b1000 : begin
        io_segments = 7'h0;
      end
      4'b1001 : begin
        io_segments = 7'h10;
      end
      4'b1010 : begin
        io_segments = 7'h08;
      end
      4'b1011 : begin
        io_segments = 7'h03;
      end
      4'b1100 : begin
        io_segments = 7'h46;
      end
      4'b1101 : begin
        io_segments = 7'h21;
      end
      4'b1110 : begin
        io_segments = 7'h06;
      end
      default : begin
        io_segments = 7'h0e;
      end
    endcase
  end


endmodule
