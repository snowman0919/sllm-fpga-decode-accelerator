// Generator : SpinalHDL v1.14.2    git head : 78f29dc66110fc099a777992b6daa2f803ab445e
// Component : UartRx
// Git hash  : dbf4dcb9a78cfcf41505e5e488bf60414ef77404

`timescale 1ns/1ps
module UartRx (
  input  wire          io_rxd,
  output wire          io_valid,
  output wire [7:0]    io_data,
  output wire          io_frameError,
  input  wire          CLOCK_50
);

  reg        [8:0]    counter;
  reg        [2:0]    bitIndex;
  reg        [7:0]    shift;
  reg                 validReg;
  reg                 frameErrorReg;
  reg        [1:0]    state;
  wire                when_UartRx_l34;
  wire                when_UartRx_l39;
  wire                when_UartRx_l41;
  wire                when_UartRx_l51;
  wire                when_UartRx_l54;
  wire                when_UartRx_l64;

  initial begin
    counter = 9'h0;
    bitIndex = 3'b000;
    shift = 8'h0;
    validReg = 1'b0;
    frameErrorReg = 1'b0;
    state = 2'b00;
  end

  assign io_valid = validReg;
  assign io_data = shift;
  assign io_frameError = frameErrorReg;
  assign when_UartRx_l34 = (! io_rxd);
  assign when_UartRx_l39 = (counter == 9'h0d8);
  assign when_UartRx_l41 = (! io_rxd);
  assign when_UartRx_l51 = (counter == 9'h1b1);
  assign when_UartRx_l54 = (bitIndex == 3'b111);
  assign when_UartRx_l64 = (counter == 9'h1b1);
  always @(posedge CLOCK_50) begin
    validReg <= 1'b0;
    frameErrorReg <= 1'b0;
    case(state)
      2'b00 : begin
        counter <= 9'h0;
        bitIndex <= 3'b000;
        if(when_UartRx_l34) begin
          state <= 2'b01;
        end
      end
      2'b01 : begin
        if(when_UartRx_l39) begin
          counter <= 9'h0;
          if(when_UartRx_l41) begin
            state <= 2'b10;
          end else begin
            state <= 2'b00;
          end
        end else begin
          counter <= (counter + 9'h001);
        end
      end
      2'b10 : begin
        if(when_UartRx_l51) begin
          counter <= 9'h0;
          shift[bitIndex] <= io_rxd;
          if(when_UartRx_l54) begin
            state <= 2'b11;
          end else begin
            bitIndex <= (bitIndex + 3'b001);
          end
        end else begin
          counter <= (counter + 9'h001);
        end
      end
      default : begin
        if(when_UartRx_l64) begin
          counter <= 9'h0;
          validReg <= io_rxd;
          frameErrorReg <= (! io_rxd);
          state <= 2'b00;
        end else begin
          counter <= (counter + 9'h001);
        end
      end
    endcase
  end


endmodule
