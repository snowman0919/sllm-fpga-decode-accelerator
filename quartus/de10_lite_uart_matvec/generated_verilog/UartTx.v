// Generator : SpinalHDL v1.14.2    git head : 78f29dc66110fc099a777992b6daa2f803ab445e
// Component : UartTx
// Git hash  : dbf4dcb9a78cfcf41505e5e488bf60414ef77404

`timescale 1ns/1ps
module UartTx (
  input  wire          io_valid,
  input  wire [7:0]    io_data,
  output wire          io_ready,
  output wire          io_txd,
  output wire          io_busy,
  input  wire          CLOCK_50
);

  wire       [2:0]    _zz_txdReg;
  reg        [8:0]    counter;
  reg        [2:0]    bitIndex;
  reg        [7:0]    shift;
  reg                 txdReg;
  reg        [1:0]    state;
  wire                when_UartTx_l39;
  wire                when_UartTx_l48;
  wire                when_UartTx_l50;
  wire                when_UartTx_l62;

  assign _zz_txdReg = (bitIndex + 3'b001);
  initial begin
    counter = 9'h0;
    bitIndex = 3'b000;
    shift = 8'h0;
    txdReg = 1'b1;
    state = 2'b00;
  end

  assign io_ready = (state == 2'b00);
  assign io_busy = (state != 2'b00);
  assign io_txd = txdReg;
  assign when_UartTx_l39 = (counter == 9'h1b1);
  assign when_UartTx_l48 = (counter == 9'h1b1);
  assign when_UartTx_l50 = (bitIndex == 3'b111);
  assign when_UartTx_l62 = (counter == 9'h1b1);
  always @(posedge CLOCK_50) begin
    case(state)
      2'b00 : begin
        txdReg <= 1'b1;
        counter <= 9'h0;
        bitIndex <= 3'b000;
        if(io_valid) begin
          shift <= io_data;
          txdReg <= 1'b0;
          state <= 2'b01;
        end
      end
      2'b01 : begin
        if(when_UartTx_l39) begin
          counter <= 9'h0;
          txdReg <= shift[0];
          state <= 2'b10;
        end else begin
          counter <= (counter + 9'h001);
        end
      end
      2'b10 : begin
        if(when_UartTx_l48) begin
          counter <= 9'h0;
          if(when_UartTx_l50) begin
            txdReg <= 1'b1;
            state <= 2'b11;
          end else begin
            bitIndex <= (bitIndex + 3'b001);
            txdReg <= shift[_zz_txdReg];
          end
        end else begin
          counter <= (counter + 9'h001);
        end
      end
      default : begin
        if(when_UartTx_l62) begin
          counter <= 9'h0;
          state <= 2'b00;
        end else begin
          counter <= (counter + 9'h001);
        end
      end
    endcase
  end


endmodule
