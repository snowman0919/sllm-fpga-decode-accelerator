// Generator : SpinalHDL v1.14.2    git head : 78f29dc66110fc099a777992b6daa2f803ab445e
// Component : DecodeMatVecInt8_i16_o4
// Git hash  : 1208ca558d19c22255120e09bbf59ad4f8340c06

`timescale 1ns/1ps
module DecodeMatVecInt8_i16_o4 (
  input  wire          io_start,
  input  wire [7:0]    io_activation_0,
  input  wire [7:0]    io_activation_1,
  input  wire [7:0]    io_activation_2,
  input  wire [7:0]    io_activation_3,
  input  wire [7:0]    io_activation_4,
  input  wire [7:0]    io_activation_5,
  input  wire [7:0]    io_activation_6,
  input  wire [7:0]    io_activation_7,
  input  wire [7:0]    io_activation_8,
  input  wire [7:0]    io_activation_9,
  input  wire [7:0]    io_activation_10,
  input  wire [7:0]    io_activation_11,
  input  wire [7:0]    io_activation_12,
  input  wire [7:0]    io_activation_13,
  input  wire [7:0]    io_activation_14,
  input  wire [7:0]    io_activation_15,
  input  wire [7:0]    io_weights_0_0,
  input  wire [7:0]    io_weights_0_1,
  input  wire [7:0]    io_weights_0_2,
  input  wire [7:0]    io_weights_0_3,
  input  wire [7:0]    io_weights_0_4,
  input  wire [7:0]    io_weights_0_5,
  input  wire [7:0]    io_weights_0_6,
  input  wire [7:0]    io_weights_0_7,
  input  wire [7:0]    io_weights_0_8,
  input  wire [7:0]    io_weights_0_9,
  input  wire [7:0]    io_weights_0_10,
  input  wire [7:0]    io_weights_0_11,
  input  wire [7:0]    io_weights_0_12,
  input  wire [7:0]    io_weights_0_13,
  input  wire [7:0]    io_weights_0_14,
  input  wire [7:0]    io_weights_0_15,
  input  wire [7:0]    io_weights_1_0,
  input  wire [7:0]    io_weights_1_1,
  input  wire [7:0]    io_weights_1_2,
  input  wire [7:0]    io_weights_1_3,
  input  wire [7:0]    io_weights_1_4,
  input  wire [7:0]    io_weights_1_5,
  input  wire [7:0]    io_weights_1_6,
  input  wire [7:0]    io_weights_1_7,
  input  wire [7:0]    io_weights_1_8,
  input  wire [7:0]    io_weights_1_9,
  input  wire [7:0]    io_weights_1_10,
  input  wire [7:0]    io_weights_1_11,
  input  wire [7:0]    io_weights_1_12,
  input  wire [7:0]    io_weights_1_13,
  input  wire [7:0]    io_weights_1_14,
  input  wire [7:0]    io_weights_1_15,
  input  wire [7:0]    io_weights_2_0,
  input  wire [7:0]    io_weights_2_1,
  input  wire [7:0]    io_weights_2_2,
  input  wire [7:0]    io_weights_2_3,
  input  wire [7:0]    io_weights_2_4,
  input  wire [7:0]    io_weights_2_5,
  input  wire [7:0]    io_weights_2_6,
  input  wire [7:0]    io_weights_2_7,
  input  wire [7:0]    io_weights_2_8,
  input  wire [7:0]    io_weights_2_9,
  input  wire [7:0]    io_weights_2_10,
  input  wire [7:0]    io_weights_2_11,
  input  wire [7:0]    io_weights_2_12,
  input  wire [7:0]    io_weights_2_13,
  input  wire [7:0]    io_weights_2_14,
  input  wire [7:0]    io_weights_2_15,
  input  wire [7:0]    io_weights_3_0,
  input  wire [7:0]    io_weights_3_1,
  input  wire [7:0]    io_weights_3_2,
  input  wire [7:0]    io_weights_3_3,
  input  wire [7:0]    io_weights_3_4,
  input  wire [7:0]    io_weights_3_5,
  input  wire [7:0]    io_weights_3_6,
  input  wire [7:0]    io_weights_3_7,
  input  wire [7:0]    io_weights_3_8,
  input  wire [7:0]    io_weights_3_9,
  input  wire [7:0]    io_weights_3_10,
  input  wire [7:0]    io_weights_3_11,
  input  wire [7:0]    io_weights_3_12,
  input  wire [7:0]    io_weights_3_13,
  input  wire [7:0]    io_weights_3_14,
  input  wire [7:0]    io_weights_3_15,
  output wire          io_busy,
  output wire          io_done,
  output wire [31:0]   io_outputs_0,
  output wire [31:0]   io_outputs_1,
  output wire [31:0]   io_outputs_2,
  output wire [31:0]   io_outputs_3,
  input  wire          CLOCK_50
);

  wire       [31:0]   _zz__zz_accReg;
  wire       [15:0]   _zz__zz_accReg_1;
  reg        [7:0]    _zz__zz_accReg_2;
  reg        [7:0]    _zz__zz_accReg_3;
  reg        [7:0]    _zz__zz_accReg_4;
  reg        [7:0]    _zz__zz_accReg_5;
  reg        [7:0]    _zz__zz_accReg_6;
  reg        [7:0]    _zz__zz_accReg_7;
  reg        [7:0]    _zz__zz_accReg_8;
  reg        [7:0]    _zz__zz_accReg_9;
  reg        [7:0]    _zz__zz_accReg_10;
  reg        [7:0]    _zz__zz_accReg_11;
  reg        [7:0]    _zz__zz_accReg_12;
  reg        [7:0]    _zz__zz_accReg_13;
  reg        [7:0]    _zz__zz_accReg_14;
  reg        [7:0]    _zz__zz_accReg_15;
  reg        [7:0]    _zz__zz_accReg_16;
  reg        [7:0]    _zz__zz_accReg_17;
  reg        [7:0]    _zz__zz_accReg_18;
  reg        [7:0]    _zz__zz_accReg_19;
  wire       [3:0]    lastInputIndex;
  wire       [1:0]    lastOutputIndex;
  reg                 busyReg;
  reg                 doneReg;
  reg        [3:0]    inputIndexReg;
  reg        [1:0]    outputIndexReg;
  reg        [31:0]   accReg;
  reg        [31:0]   outputRegs_0;
  reg        [31:0]   outputRegs_1;
  reg        [31:0]   outputRegs_2;
  reg        [31:0]   outputRegs_3;
  wire                when_DecodeMatVecInt8_l94;
  wire       [31:0]   _zz_accReg;
  wire                when_DecodeMatVecInt8_l106;
  wire       [3:0]    _zz_1;
  wire                when_DecodeMatVecInt8_l111;

  assign _zz__zz_accReg_1 = ($signed(_zz__zz_accReg_2) * $signed(_zz__zz_accReg_3));
  assign _zz__zz_accReg = {{16{_zz__zz_accReg_1[15]}}, _zz__zz_accReg_1};
  initial begin
    busyReg = 1'b0;
    doneReg = 1'b0;
    inputIndexReg = 4'b0000;
    outputIndexReg = 2'b00;
    accReg = 32'h0;
    outputRegs_0 = 32'h0;
    outputRegs_1 = 32'h0;
    outputRegs_2 = 32'h0;
    outputRegs_3 = 32'h0;
  end

  always @(*) begin
    case(inputIndexReg)
      4'b0000 : begin
        _zz__zz_accReg_2 = io_activation_0;
        _zz__zz_accReg_3 = _zz__zz_accReg_4;
      end
      4'b0001 : begin
        _zz__zz_accReg_2 = io_activation_1;
        _zz__zz_accReg_3 = _zz__zz_accReg_5;
      end
      4'b0010 : begin
        _zz__zz_accReg_2 = io_activation_2;
        _zz__zz_accReg_3 = _zz__zz_accReg_6;
      end
      4'b0011 : begin
        _zz__zz_accReg_2 = io_activation_3;
        _zz__zz_accReg_3 = _zz__zz_accReg_7;
      end
      4'b0100 : begin
        _zz__zz_accReg_2 = io_activation_4;
        _zz__zz_accReg_3 = _zz__zz_accReg_8;
      end
      4'b0101 : begin
        _zz__zz_accReg_2 = io_activation_5;
        _zz__zz_accReg_3 = _zz__zz_accReg_9;
      end
      4'b0110 : begin
        _zz__zz_accReg_2 = io_activation_6;
        _zz__zz_accReg_3 = _zz__zz_accReg_10;
      end
      4'b0111 : begin
        _zz__zz_accReg_2 = io_activation_7;
        _zz__zz_accReg_3 = _zz__zz_accReg_11;
      end
      4'b1000 : begin
        _zz__zz_accReg_2 = io_activation_8;
        _zz__zz_accReg_3 = _zz__zz_accReg_12;
      end
      4'b1001 : begin
        _zz__zz_accReg_2 = io_activation_9;
        _zz__zz_accReg_3 = _zz__zz_accReg_13;
      end
      4'b1010 : begin
        _zz__zz_accReg_2 = io_activation_10;
        _zz__zz_accReg_3 = _zz__zz_accReg_14;
      end
      4'b1011 : begin
        _zz__zz_accReg_2 = io_activation_11;
        _zz__zz_accReg_3 = _zz__zz_accReg_15;
      end
      4'b1100 : begin
        _zz__zz_accReg_2 = io_activation_12;
        _zz__zz_accReg_3 = _zz__zz_accReg_16;
      end
      4'b1101 : begin
        _zz__zz_accReg_2 = io_activation_13;
        _zz__zz_accReg_3 = _zz__zz_accReg_17;
      end
      4'b1110 : begin
        _zz__zz_accReg_2 = io_activation_14;
        _zz__zz_accReg_3 = _zz__zz_accReg_18;
      end
      default : begin
        _zz__zz_accReg_2 = io_activation_15;
        _zz__zz_accReg_3 = _zz__zz_accReg_19;
      end
    endcase
  end

  always @(*) begin
    case(outputIndexReg)
      2'b00 : begin
        _zz__zz_accReg_4 = io_weights_0_0;
        _zz__zz_accReg_5 = io_weights_0_1;
        _zz__zz_accReg_6 = io_weights_0_2;
        _zz__zz_accReg_7 = io_weights_0_3;
        _zz__zz_accReg_8 = io_weights_0_4;
        _zz__zz_accReg_9 = io_weights_0_5;
        _zz__zz_accReg_10 = io_weights_0_6;
        _zz__zz_accReg_11 = io_weights_0_7;
        _zz__zz_accReg_12 = io_weights_0_8;
        _zz__zz_accReg_13 = io_weights_0_9;
        _zz__zz_accReg_14 = io_weights_0_10;
        _zz__zz_accReg_15 = io_weights_0_11;
        _zz__zz_accReg_16 = io_weights_0_12;
        _zz__zz_accReg_17 = io_weights_0_13;
        _zz__zz_accReg_18 = io_weights_0_14;
        _zz__zz_accReg_19 = io_weights_0_15;
      end
      2'b01 : begin
        _zz__zz_accReg_4 = io_weights_1_0;
        _zz__zz_accReg_5 = io_weights_1_1;
        _zz__zz_accReg_6 = io_weights_1_2;
        _zz__zz_accReg_7 = io_weights_1_3;
        _zz__zz_accReg_8 = io_weights_1_4;
        _zz__zz_accReg_9 = io_weights_1_5;
        _zz__zz_accReg_10 = io_weights_1_6;
        _zz__zz_accReg_11 = io_weights_1_7;
        _zz__zz_accReg_12 = io_weights_1_8;
        _zz__zz_accReg_13 = io_weights_1_9;
        _zz__zz_accReg_14 = io_weights_1_10;
        _zz__zz_accReg_15 = io_weights_1_11;
        _zz__zz_accReg_16 = io_weights_1_12;
        _zz__zz_accReg_17 = io_weights_1_13;
        _zz__zz_accReg_18 = io_weights_1_14;
        _zz__zz_accReg_19 = io_weights_1_15;
      end
      2'b10 : begin
        _zz__zz_accReg_4 = io_weights_2_0;
        _zz__zz_accReg_5 = io_weights_2_1;
        _zz__zz_accReg_6 = io_weights_2_2;
        _zz__zz_accReg_7 = io_weights_2_3;
        _zz__zz_accReg_8 = io_weights_2_4;
        _zz__zz_accReg_9 = io_weights_2_5;
        _zz__zz_accReg_10 = io_weights_2_6;
        _zz__zz_accReg_11 = io_weights_2_7;
        _zz__zz_accReg_12 = io_weights_2_8;
        _zz__zz_accReg_13 = io_weights_2_9;
        _zz__zz_accReg_14 = io_weights_2_10;
        _zz__zz_accReg_15 = io_weights_2_11;
        _zz__zz_accReg_16 = io_weights_2_12;
        _zz__zz_accReg_17 = io_weights_2_13;
        _zz__zz_accReg_18 = io_weights_2_14;
        _zz__zz_accReg_19 = io_weights_2_15;
      end
      default : begin
        _zz__zz_accReg_4 = io_weights_3_0;
        _zz__zz_accReg_5 = io_weights_3_1;
        _zz__zz_accReg_6 = io_weights_3_2;
        _zz__zz_accReg_7 = io_weights_3_3;
        _zz__zz_accReg_8 = io_weights_3_4;
        _zz__zz_accReg_9 = io_weights_3_5;
        _zz__zz_accReg_10 = io_weights_3_6;
        _zz__zz_accReg_11 = io_weights_3_7;
        _zz__zz_accReg_12 = io_weights_3_8;
        _zz__zz_accReg_13 = io_weights_3_9;
        _zz__zz_accReg_14 = io_weights_3_10;
        _zz__zz_accReg_15 = io_weights_3_11;
        _zz__zz_accReg_16 = io_weights_3_12;
        _zz__zz_accReg_17 = io_weights_3_13;
        _zz__zz_accReg_18 = io_weights_3_14;
        _zz__zz_accReg_19 = io_weights_3_15;
      end
    endcase
  end

  assign lastInputIndex = 4'b1111;
  assign lastOutputIndex = 2'b11;
  assign io_busy = busyReg;
  assign io_done = doneReg;
  assign io_outputs_0 = outputRegs_0;
  assign io_outputs_1 = outputRegs_1;
  assign io_outputs_2 = outputRegs_2;
  assign io_outputs_3 = outputRegs_3;
  assign when_DecodeMatVecInt8_l94 = (io_start && (! busyReg));
  assign _zz_accReg = ($signed(accReg) + $signed(_zz__zz_accReg));
  assign when_DecodeMatVecInt8_l106 = (inputIndexReg == lastInputIndex);
  assign _zz_1 = ({3'd0,1'b1} <<< outputIndexReg);
  assign when_DecodeMatVecInt8_l111 = (outputIndexReg == lastOutputIndex);
  always @(posedge CLOCK_50) begin
    doneReg <= 1'b0;
    if(when_DecodeMatVecInt8_l94) begin
      busyReg <= 1'b1;
      inputIndexReg <= 4'b0000;
      outputIndexReg <= 2'b00;
      accReg <= 32'h0;
      outputRegs_0 <= 32'h0;
      outputRegs_1 <= 32'h0;
      outputRegs_2 <= 32'h0;
      outputRegs_3 <= 32'h0;
    end else begin
      if(busyReg) begin
        if(when_DecodeMatVecInt8_l106) begin
          if(_zz_1[0]) begin
            outputRegs_0 <= _zz_accReg;
          end
          if(_zz_1[1]) begin
            outputRegs_1 <= _zz_accReg;
          end
          if(_zz_1[2]) begin
            outputRegs_2 <= _zz_accReg;
          end
          if(_zz_1[3]) begin
            outputRegs_3 <= _zz_accReg;
          end
          accReg <= 32'h0;
          inputIndexReg <= 4'b0000;
          if(when_DecodeMatVecInt8_l111) begin
            busyReg <= 1'b0;
            doneReg <= 1'b1;
          end else begin
            outputIndexReg <= (outputIndexReg + 2'b01);
          end
        end else begin
          accReg <= _zz_accReg;
          inputIndexReg <= (inputIndexReg + 4'b0001);
        end
      end
    end
  end


endmodule
