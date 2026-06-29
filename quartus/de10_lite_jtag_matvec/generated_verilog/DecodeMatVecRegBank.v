// Generator : SpinalHDL v1.14.2    git head : 78f29dc66110fc099a777992b6daa2f803ab445e
// Component : DecodeMatVecRegBank
// Git hash  : 1208ca558d19c22255120e09bbf59ad4f8340c06

`timescale 1ns/1ps
module DecodeMatVecRegBank (
  input  wire [11:0]   io_address,
  input  wire          io_read,
  input  wire          io_write,
  input  wire [31:0]   io_writedata,
  output wire [31:0]   io_readdata,
  output wire          io_waitrequest,
  output wire          io_readdatavalid,
  output reg  [7:0]    io_debugStatus,
  output wire [7:0]    io_debugSeq,
  input  wire          CLOCK_50
);

  wire                matVec_io_busy;
  wire                matVec_io_done;
  wire       [31:0]   matVec_io_outputs_0;
  wire       [31:0]   matVec_io_outputs_1;
  wire       [31:0]   matVec_io_outputs_2;
  wire       [31:0]   matVec_io_outputs_3;
  reg        [7:0]    _zz_readData;
  wire       [3:0]    _zz_readData_1;
  wire       [9:0]    _zz_readData_2;
  reg        [7:0]    _zz_readData_3;
  wire       [5:0]    _zz_readData_4;
  wire       [9:0]    _zz_readData_5;
  reg        [31:0]   _zz_readData_6;
  wire       [1:0]    _zz_readData_7;
  wire       [9:0]    _zz_readData_8;
  wire       [3:0]    _zz__zz_1;
  wire       [9:0]    _zz__zz_1_1;
  wire       [5:0]    _zz__zz_2;
  wire       [9:0]    _zz__zz_2_1;
  reg        [7:0]    activationRegs_0;
  reg        [7:0]    activationRegs_1;
  reg        [7:0]    activationRegs_2;
  reg        [7:0]    activationRegs_3;
  reg        [7:0]    activationRegs_4;
  reg        [7:0]    activationRegs_5;
  reg        [7:0]    activationRegs_6;
  reg        [7:0]    activationRegs_7;
  reg        [7:0]    activationRegs_8;
  reg        [7:0]    activationRegs_9;
  reg        [7:0]    activationRegs_10;
  reg        [7:0]    activationRegs_11;
  reg        [7:0]    activationRegs_12;
  reg        [7:0]    activationRegs_13;
  reg        [7:0]    activationRegs_14;
  reg        [7:0]    activationRegs_15;
  reg        [7:0]    weightRegs_0;
  reg        [7:0]    weightRegs_1;
  reg        [7:0]    weightRegs_2;
  reg        [7:0]    weightRegs_3;
  reg        [7:0]    weightRegs_4;
  reg        [7:0]    weightRegs_5;
  reg        [7:0]    weightRegs_6;
  reg        [7:0]    weightRegs_7;
  reg        [7:0]    weightRegs_8;
  reg        [7:0]    weightRegs_9;
  reg        [7:0]    weightRegs_10;
  reg        [7:0]    weightRegs_11;
  reg        [7:0]    weightRegs_12;
  reg        [7:0]    weightRegs_13;
  reg        [7:0]    weightRegs_14;
  reg        [7:0]    weightRegs_15;
  reg        [7:0]    weightRegs_16;
  reg        [7:0]    weightRegs_17;
  reg        [7:0]    weightRegs_18;
  reg        [7:0]    weightRegs_19;
  reg        [7:0]    weightRegs_20;
  reg        [7:0]    weightRegs_21;
  reg        [7:0]    weightRegs_22;
  reg        [7:0]    weightRegs_23;
  reg        [7:0]    weightRegs_24;
  reg        [7:0]    weightRegs_25;
  reg        [7:0]    weightRegs_26;
  reg        [7:0]    weightRegs_27;
  reg        [7:0]    weightRegs_28;
  reg        [7:0]    weightRegs_29;
  reg        [7:0]    weightRegs_30;
  reg        [7:0]    weightRegs_31;
  reg        [7:0]    weightRegs_32;
  reg        [7:0]    weightRegs_33;
  reg        [7:0]    weightRegs_34;
  reg        [7:0]    weightRegs_35;
  reg        [7:0]    weightRegs_36;
  reg        [7:0]    weightRegs_37;
  reg        [7:0]    weightRegs_38;
  reg        [7:0]    weightRegs_39;
  reg        [7:0]    weightRegs_40;
  reg        [7:0]    weightRegs_41;
  reg        [7:0]    weightRegs_42;
  reg        [7:0]    weightRegs_43;
  reg        [7:0]    weightRegs_44;
  reg        [7:0]    weightRegs_45;
  reg        [7:0]    weightRegs_46;
  reg        [7:0]    weightRegs_47;
  reg        [7:0]    weightRegs_48;
  reg        [7:0]    weightRegs_49;
  reg        [7:0]    weightRegs_50;
  reg        [7:0]    weightRegs_51;
  reg        [7:0]    weightRegs_52;
  reg        [7:0]    weightRegs_53;
  reg        [7:0]    weightRegs_54;
  reg        [7:0]    weightRegs_55;
  reg        [7:0]    weightRegs_56;
  reg        [7:0]    weightRegs_57;
  reg        [7:0]    weightRegs_58;
  reg        [7:0]    weightRegs_59;
  reg        [7:0]    weightRegs_60;
  reg        [7:0]    weightRegs_61;
  reg        [7:0]    weightRegs_62;
  reg        [7:0]    weightRegs_63;
  reg                 doneLatched;
  reg                 errorReg;
  reg        [31:0]   seqReg;
  reg                 startPulse;
  reg                 io_read_regNext;
  wire       [9:0]    wordAddress;
  reg        [31:0]   readData;
  wire                when_DecodeMatVecRegBank_l72;
  wire                when_DecodeMatVecRegBank_l76;
  wire                when_DecodeMatVecRegBank_l78;
  wire                when_DecodeMatVecRegBank_l80;
  wire                when_DecodeMatVecRegBank_l86;
  wire                when_DecodeMatVecRegBank_l92;
  wire                when_DecodeMatVecRegBank_l102;
  wire                when_DecodeMatVecRegBank_l103;
  wire                when_DecodeMatVecRegBank_l107;
  wire                when_DecodeMatVecRegBank_l110;
  wire       [15:0]   _zz_1;
  wire       [7:0]    _zz_activationRegs_0;
  wire       [63:0]   _zz_2;
  wire       [7:0]    _zz_weightRegs_0;
  wire                when_DecodeMatVecRegBank_l119;
  wire                when_DecodeMatVecRegBank_l121;
  wire                when_DecodeMatVecRegBank_l127;

  assign _zz_readData_2 = (wordAddress - 10'h040);
  assign _zz_readData_1 = _zz_readData_2[3:0];
  assign _zz_readData_5 = (wordAddress - 10'h080);
  assign _zz_readData_4 = _zz_readData_5[5:0];
  assign _zz_readData_8 = (wordAddress - 10'h0c0);
  assign _zz_readData_7 = _zz_readData_8[1:0];
  assign _zz__zz_1_1 = (wordAddress - 10'h040);
  assign _zz__zz_1 = _zz__zz_1_1[3:0];
  assign _zz__zz_2_1 = (wordAddress - 10'h080);
  assign _zz__zz_2 = _zz__zz_2_1[5:0];
  DecodeMatVecInt8_i16_o4 matVec (
    .io_start         (startPulse               ), //i
    .io_activation_0  (activationRegs_0[7:0]    ), //i
    .io_activation_1  (activationRegs_1[7:0]    ), //i
    .io_activation_2  (activationRegs_2[7:0]    ), //i
    .io_activation_3  (activationRegs_3[7:0]    ), //i
    .io_activation_4  (activationRegs_4[7:0]    ), //i
    .io_activation_5  (activationRegs_5[7:0]    ), //i
    .io_activation_6  (activationRegs_6[7:0]    ), //i
    .io_activation_7  (activationRegs_7[7:0]    ), //i
    .io_activation_8  (activationRegs_8[7:0]    ), //i
    .io_activation_9  (activationRegs_9[7:0]    ), //i
    .io_activation_10 (activationRegs_10[7:0]   ), //i
    .io_activation_11 (activationRegs_11[7:0]   ), //i
    .io_activation_12 (activationRegs_12[7:0]   ), //i
    .io_activation_13 (activationRegs_13[7:0]   ), //i
    .io_activation_14 (activationRegs_14[7:0]   ), //i
    .io_activation_15 (activationRegs_15[7:0]   ), //i
    .io_weights_0_0   (weightRegs_0[7:0]        ), //i
    .io_weights_0_1   (weightRegs_1[7:0]        ), //i
    .io_weights_0_2   (weightRegs_2[7:0]        ), //i
    .io_weights_0_3   (weightRegs_3[7:0]        ), //i
    .io_weights_0_4   (weightRegs_4[7:0]        ), //i
    .io_weights_0_5   (weightRegs_5[7:0]        ), //i
    .io_weights_0_6   (weightRegs_6[7:0]        ), //i
    .io_weights_0_7   (weightRegs_7[7:0]        ), //i
    .io_weights_0_8   (weightRegs_8[7:0]        ), //i
    .io_weights_0_9   (weightRegs_9[7:0]        ), //i
    .io_weights_0_10  (weightRegs_10[7:0]       ), //i
    .io_weights_0_11  (weightRegs_11[7:0]       ), //i
    .io_weights_0_12  (weightRegs_12[7:0]       ), //i
    .io_weights_0_13  (weightRegs_13[7:0]       ), //i
    .io_weights_0_14  (weightRegs_14[7:0]       ), //i
    .io_weights_0_15  (weightRegs_15[7:0]       ), //i
    .io_weights_1_0   (weightRegs_16[7:0]       ), //i
    .io_weights_1_1   (weightRegs_17[7:0]       ), //i
    .io_weights_1_2   (weightRegs_18[7:0]       ), //i
    .io_weights_1_3   (weightRegs_19[7:0]       ), //i
    .io_weights_1_4   (weightRegs_20[7:0]       ), //i
    .io_weights_1_5   (weightRegs_21[7:0]       ), //i
    .io_weights_1_6   (weightRegs_22[7:0]       ), //i
    .io_weights_1_7   (weightRegs_23[7:0]       ), //i
    .io_weights_1_8   (weightRegs_24[7:0]       ), //i
    .io_weights_1_9   (weightRegs_25[7:0]       ), //i
    .io_weights_1_10  (weightRegs_26[7:0]       ), //i
    .io_weights_1_11  (weightRegs_27[7:0]       ), //i
    .io_weights_1_12  (weightRegs_28[7:0]       ), //i
    .io_weights_1_13  (weightRegs_29[7:0]       ), //i
    .io_weights_1_14  (weightRegs_30[7:0]       ), //i
    .io_weights_1_15  (weightRegs_31[7:0]       ), //i
    .io_weights_2_0   (weightRegs_32[7:0]       ), //i
    .io_weights_2_1   (weightRegs_33[7:0]       ), //i
    .io_weights_2_2   (weightRegs_34[7:0]       ), //i
    .io_weights_2_3   (weightRegs_35[7:0]       ), //i
    .io_weights_2_4   (weightRegs_36[7:0]       ), //i
    .io_weights_2_5   (weightRegs_37[7:0]       ), //i
    .io_weights_2_6   (weightRegs_38[7:0]       ), //i
    .io_weights_2_7   (weightRegs_39[7:0]       ), //i
    .io_weights_2_8   (weightRegs_40[7:0]       ), //i
    .io_weights_2_9   (weightRegs_41[7:0]       ), //i
    .io_weights_2_10  (weightRegs_42[7:0]       ), //i
    .io_weights_2_11  (weightRegs_43[7:0]       ), //i
    .io_weights_2_12  (weightRegs_44[7:0]       ), //i
    .io_weights_2_13  (weightRegs_45[7:0]       ), //i
    .io_weights_2_14  (weightRegs_46[7:0]       ), //i
    .io_weights_2_15  (weightRegs_47[7:0]       ), //i
    .io_weights_3_0   (weightRegs_48[7:0]       ), //i
    .io_weights_3_1   (weightRegs_49[7:0]       ), //i
    .io_weights_3_2   (weightRegs_50[7:0]       ), //i
    .io_weights_3_3   (weightRegs_51[7:0]       ), //i
    .io_weights_3_4   (weightRegs_52[7:0]       ), //i
    .io_weights_3_5   (weightRegs_53[7:0]       ), //i
    .io_weights_3_6   (weightRegs_54[7:0]       ), //i
    .io_weights_3_7   (weightRegs_55[7:0]       ), //i
    .io_weights_3_8   (weightRegs_56[7:0]       ), //i
    .io_weights_3_9   (weightRegs_57[7:0]       ), //i
    .io_weights_3_10  (weightRegs_58[7:0]       ), //i
    .io_weights_3_11  (weightRegs_59[7:0]       ), //i
    .io_weights_3_12  (weightRegs_60[7:0]       ), //i
    .io_weights_3_13  (weightRegs_61[7:0]       ), //i
    .io_weights_3_14  (weightRegs_62[7:0]       ), //i
    .io_weights_3_15  (weightRegs_63[7:0]       ), //i
    .io_busy          (matVec_io_busy           ), //o
    .io_done          (matVec_io_done           ), //o
    .io_outputs_0     (matVec_io_outputs_0[31:0]), //o
    .io_outputs_1     (matVec_io_outputs_1[31:0]), //o
    .io_outputs_2     (matVec_io_outputs_2[31:0]), //o
    .io_outputs_3     (matVec_io_outputs_3[31:0]), //o
    .CLOCK_50         (CLOCK_50                 )  //i
  );
  initial begin
    activationRegs_0 = 8'h0;
    activationRegs_1 = 8'h0;
    activationRegs_2 = 8'h0;
    activationRegs_3 = 8'h0;
    activationRegs_4 = 8'h0;
    activationRegs_5 = 8'h0;
    activationRegs_6 = 8'h0;
    activationRegs_7 = 8'h0;
    activationRegs_8 = 8'h0;
    activationRegs_9 = 8'h0;
    activationRegs_10 = 8'h0;
    activationRegs_11 = 8'h0;
    activationRegs_12 = 8'h0;
    activationRegs_13 = 8'h0;
    activationRegs_14 = 8'h0;
    activationRegs_15 = 8'h0;
    weightRegs_0 = 8'h0;
    weightRegs_1 = 8'h0;
    weightRegs_2 = 8'h0;
    weightRegs_3 = 8'h0;
    weightRegs_4 = 8'h0;
    weightRegs_5 = 8'h0;
    weightRegs_6 = 8'h0;
    weightRegs_7 = 8'h0;
    weightRegs_8 = 8'h0;
    weightRegs_9 = 8'h0;
    weightRegs_10 = 8'h0;
    weightRegs_11 = 8'h0;
    weightRegs_12 = 8'h0;
    weightRegs_13 = 8'h0;
    weightRegs_14 = 8'h0;
    weightRegs_15 = 8'h0;
    weightRegs_16 = 8'h0;
    weightRegs_17 = 8'h0;
    weightRegs_18 = 8'h0;
    weightRegs_19 = 8'h0;
    weightRegs_20 = 8'h0;
    weightRegs_21 = 8'h0;
    weightRegs_22 = 8'h0;
    weightRegs_23 = 8'h0;
    weightRegs_24 = 8'h0;
    weightRegs_25 = 8'h0;
    weightRegs_26 = 8'h0;
    weightRegs_27 = 8'h0;
    weightRegs_28 = 8'h0;
    weightRegs_29 = 8'h0;
    weightRegs_30 = 8'h0;
    weightRegs_31 = 8'h0;
    weightRegs_32 = 8'h0;
    weightRegs_33 = 8'h0;
    weightRegs_34 = 8'h0;
    weightRegs_35 = 8'h0;
    weightRegs_36 = 8'h0;
    weightRegs_37 = 8'h0;
    weightRegs_38 = 8'h0;
    weightRegs_39 = 8'h0;
    weightRegs_40 = 8'h0;
    weightRegs_41 = 8'h0;
    weightRegs_42 = 8'h0;
    weightRegs_43 = 8'h0;
    weightRegs_44 = 8'h0;
    weightRegs_45 = 8'h0;
    weightRegs_46 = 8'h0;
    weightRegs_47 = 8'h0;
    weightRegs_48 = 8'h0;
    weightRegs_49 = 8'h0;
    weightRegs_50 = 8'h0;
    weightRegs_51 = 8'h0;
    weightRegs_52 = 8'h0;
    weightRegs_53 = 8'h0;
    weightRegs_54 = 8'h0;
    weightRegs_55 = 8'h0;
    weightRegs_56 = 8'h0;
    weightRegs_57 = 8'h0;
    weightRegs_58 = 8'h0;
    weightRegs_59 = 8'h0;
    weightRegs_60 = 8'h0;
    weightRegs_61 = 8'h0;
    weightRegs_62 = 8'h0;
    weightRegs_63 = 8'h0;
    doneLatched = 1'b0;
    errorReg = 1'b0;
    seqReg = 32'h0;
    startPulse = 1'b0;
    io_read_regNext = 1'b0;
  end

  always @(*) begin
    case(_zz_readData_1)
      4'b0000 : _zz_readData = activationRegs_0;
      4'b0001 : _zz_readData = activationRegs_1;
      4'b0010 : _zz_readData = activationRegs_2;
      4'b0011 : _zz_readData = activationRegs_3;
      4'b0100 : _zz_readData = activationRegs_4;
      4'b0101 : _zz_readData = activationRegs_5;
      4'b0110 : _zz_readData = activationRegs_6;
      4'b0111 : _zz_readData = activationRegs_7;
      4'b1000 : _zz_readData = activationRegs_8;
      4'b1001 : _zz_readData = activationRegs_9;
      4'b1010 : _zz_readData = activationRegs_10;
      4'b1011 : _zz_readData = activationRegs_11;
      4'b1100 : _zz_readData = activationRegs_12;
      4'b1101 : _zz_readData = activationRegs_13;
      4'b1110 : _zz_readData = activationRegs_14;
      default : _zz_readData = activationRegs_15;
    endcase
  end

  always @(*) begin
    case(_zz_readData_4)
      6'b000000 : _zz_readData_3 = weightRegs_0;
      6'b000001 : _zz_readData_3 = weightRegs_1;
      6'b000010 : _zz_readData_3 = weightRegs_2;
      6'b000011 : _zz_readData_3 = weightRegs_3;
      6'b000100 : _zz_readData_3 = weightRegs_4;
      6'b000101 : _zz_readData_3 = weightRegs_5;
      6'b000110 : _zz_readData_3 = weightRegs_6;
      6'b000111 : _zz_readData_3 = weightRegs_7;
      6'b001000 : _zz_readData_3 = weightRegs_8;
      6'b001001 : _zz_readData_3 = weightRegs_9;
      6'b001010 : _zz_readData_3 = weightRegs_10;
      6'b001011 : _zz_readData_3 = weightRegs_11;
      6'b001100 : _zz_readData_3 = weightRegs_12;
      6'b001101 : _zz_readData_3 = weightRegs_13;
      6'b001110 : _zz_readData_3 = weightRegs_14;
      6'b001111 : _zz_readData_3 = weightRegs_15;
      6'b010000 : _zz_readData_3 = weightRegs_16;
      6'b010001 : _zz_readData_3 = weightRegs_17;
      6'b010010 : _zz_readData_3 = weightRegs_18;
      6'b010011 : _zz_readData_3 = weightRegs_19;
      6'b010100 : _zz_readData_3 = weightRegs_20;
      6'b010101 : _zz_readData_3 = weightRegs_21;
      6'b010110 : _zz_readData_3 = weightRegs_22;
      6'b010111 : _zz_readData_3 = weightRegs_23;
      6'b011000 : _zz_readData_3 = weightRegs_24;
      6'b011001 : _zz_readData_3 = weightRegs_25;
      6'b011010 : _zz_readData_3 = weightRegs_26;
      6'b011011 : _zz_readData_3 = weightRegs_27;
      6'b011100 : _zz_readData_3 = weightRegs_28;
      6'b011101 : _zz_readData_3 = weightRegs_29;
      6'b011110 : _zz_readData_3 = weightRegs_30;
      6'b011111 : _zz_readData_3 = weightRegs_31;
      6'b100000 : _zz_readData_3 = weightRegs_32;
      6'b100001 : _zz_readData_3 = weightRegs_33;
      6'b100010 : _zz_readData_3 = weightRegs_34;
      6'b100011 : _zz_readData_3 = weightRegs_35;
      6'b100100 : _zz_readData_3 = weightRegs_36;
      6'b100101 : _zz_readData_3 = weightRegs_37;
      6'b100110 : _zz_readData_3 = weightRegs_38;
      6'b100111 : _zz_readData_3 = weightRegs_39;
      6'b101000 : _zz_readData_3 = weightRegs_40;
      6'b101001 : _zz_readData_3 = weightRegs_41;
      6'b101010 : _zz_readData_3 = weightRegs_42;
      6'b101011 : _zz_readData_3 = weightRegs_43;
      6'b101100 : _zz_readData_3 = weightRegs_44;
      6'b101101 : _zz_readData_3 = weightRegs_45;
      6'b101110 : _zz_readData_3 = weightRegs_46;
      6'b101111 : _zz_readData_3 = weightRegs_47;
      6'b110000 : _zz_readData_3 = weightRegs_48;
      6'b110001 : _zz_readData_3 = weightRegs_49;
      6'b110010 : _zz_readData_3 = weightRegs_50;
      6'b110011 : _zz_readData_3 = weightRegs_51;
      6'b110100 : _zz_readData_3 = weightRegs_52;
      6'b110101 : _zz_readData_3 = weightRegs_53;
      6'b110110 : _zz_readData_3 = weightRegs_54;
      6'b110111 : _zz_readData_3 = weightRegs_55;
      6'b111000 : _zz_readData_3 = weightRegs_56;
      6'b111001 : _zz_readData_3 = weightRegs_57;
      6'b111010 : _zz_readData_3 = weightRegs_58;
      6'b111011 : _zz_readData_3 = weightRegs_59;
      6'b111100 : _zz_readData_3 = weightRegs_60;
      6'b111101 : _zz_readData_3 = weightRegs_61;
      6'b111110 : _zz_readData_3 = weightRegs_62;
      default : _zz_readData_3 = weightRegs_63;
    endcase
  end

  always @(*) begin
    case(_zz_readData_7)
      2'b00 : _zz_readData_6 = matVec_io_outputs_0;
      2'b01 : _zz_readData_6 = matVec_io_outputs_1;
      2'b10 : _zz_readData_6 = matVec_io_outputs_2;
      default : _zz_readData_6 = matVec_io_outputs_3;
    endcase
  end

  assign io_waitrequest = 1'b0;
  assign io_readdatavalid = io_read_regNext;
  assign io_debugSeq = seqReg[7 : 0];
  always @(*) begin
    io_debugStatus = 8'h0;
    io_debugStatus[0] = matVec_io_busy;
    io_debugStatus[1] = doneLatched;
    io_debugStatus[2] = errorReg;
  end

  assign wordAddress = io_address[11 : 2];
  always @(*) begin
    readData = 32'h0;
    if(when_DecodeMatVecRegBank_l72) begin
      readData[0] = matVec_io_busy;
      readData[1] = doneLatched;
      readData[2] = errorReg;
    end else begin
      if(when_DecodeMatVecRegBank_l76) begin
        readData = 32'h00040010;
      end else begin
        if(when_DecodeMatVecRegBank_l78) begin
          readData = seqReg;
        end else begin
          if(when_DecodeMatVecRegBank_l80) begin
            readData[7 : 0] = _zz_readData;
          end else begin
            if(when_DecodeMatVecRegBank_l86) begin
              readData[7 : 0] = _zz_readData_3;
            end else begin
              if(when_DecodeMatVecRegBank_l92) begin
                readData = _zz_readData_6;
              end
            end
          end
        end
      end
    end
  end

  assign when_DecodeMatVecRegBank_l72 = (wordAddress == 10'h001);
  assign when_DecodeMatVecRegBank_l76 = (wordAddress == 10'h002);
  assign when_DecodeMatVecRegBank_l78 = (wordAddress == 10'h004);
  assign when_DecodeMatVecRegBank_l80 = ((10'h040 <= wordAddress) && (wordAddress < 10'h050));
  assign when_DecodeMatVecRegBank_l86 = ((10'h080 <= wordAddress) && (wordAddress < 10'h0c0));
  assign when_DecodeMatVecRegBank_l92 = ((10'h0c0 <= wordAddress) && (wordAddress < 10'h0c4));
  assign io_readdata = readData;
  assign when_DecodeMatVecRegBank_l102 = (wordAddress == 10'h0);
  assign when_DecodeMatVecRegBank_l103 = io_writedata[1];
  assign when_DecodeMatVecRegBank_l107 = io_writedata[2];
  assign when_DecodeMatVecRegBank_l110 = io_writedata[0];
  assign _zz_1 = ({15'd0,1'b1} <<< _zz__zz_1);
  assign _zz_activationRegs_0 = io_writedata[7 : 0];
  assign _zz_2 = ({63'd0,1'b1} <<< _zz__zz_2);
  assign _zz_weightRegs_0 = io_writedata[7 : 0];
  assign when_DecodeMatVecRegBank_l119 = (wordAddress == 10'h004);
  assign when_DecodeMatVecRegBank_l121 = ((10'h040 <= wordAddress) && (wordAddress < 10'h050));
  assign when_DecodeMatVecRegBank_l127 = ((10'h080 <= wordAddress) && (wordAddress < 10'h0c0));
  always @(posedge CLOCK_50) begin
    startPulse <= 1'b0;
    if(matVec_io_done) begin
      doneLatched <= 1'b1;
    end
    io_read_regNext <= io_read;
    if(io_write) begin
      if(when_DecodeMatVecRegBank_l102) begin
        if(when_DecodeMatVecRegBank_l103) begin
          doneLatched <= 1'b0;
          errorReg <= 1'b0;
        end
        if(when_DecodeMatVecRegBank_l107) begin
          doneLatched <= 1'b0;
        end
        if(when_DecodeMatVecRegBank_l110) begin
          if(matVec_io_busy) begin
            errorReg <= 1'b1;
          end else begin
            doneLatched <= 1'b0;
            errorReg <= 1'b0;
            startPulse <= 1'b1;
          end
        end
      end else begin
        if(when_DecodeMatVecRegBank_l119) begin
          seqReg <= io_writedata;
        end else begin
          if(when_DecodeMatVecRegBank_l121) begin
            if(_zz_1[0]) begin
              activationRegs_0 <= _zz_activationRegs_0;
            end
            if(_zz_1[1]) begin
              activationRegs_1 <= _zz_activationRegs_0;
            end
            if(_zz_1[2]) begin
              activationRegs_2 <= _zz_activationRegs_0;
            end
            if(_zz_1[3]) begin
              activationRegs_3 <= _zz_activationRegs_0;
            end
            if(_zz_1[4]) begin
              activationRegs_4 <= _zz_activationRegs_0;
            end
            if(_zz_1[5]) begin
              activationRegs_5 <= _zz_activationRegs_0;
            end
            if(_zz_1[6]) begin
              activationRegs_6 <= _zz_activationRegs_0;
            end
            if(_zz_1[7]) begin
              activationRegs_7 <= _zz_activationRegs_0;
            end
            if(_zz_1[8]) begin
              activationRegs_8 <= _zz_activationRegs_0;
            end
            if(_zz_1[9]) begin
              activationRegs_9 <= _zz_activationRegs_0;
            end
            if(_zz_1[10]) begin
              activationRegs_10 <= _zz_activationRegs_0;
            end
            if(_zz_1[11]) begin
              activationRegs_11 <= _zz_activationRegs_0;
            end
            if(_zz_1[12]) begin
              activationRegs_12 <= _zz_activationRegs_0;
            end
            if(_zz_1[13]) begin
              activationRegs_13 <= _zz_activationRegs_0;
            end
            if(_zz_1[14]) begin
              activationRegs_14 <= _zz_activationRegs_0;
            end
            if(_zz_1[15]) begin
              activationRegs_15 <= _zz_activationRegs_0;
            end
          end else begin
            if(when_DecodeMatVecRegBank_l127) begin
              if(_zz_2[0]) begin
                weightRegs_0 <= _zz_weightRegs_0;
              end
              if(_zz_2[1]) begin
                weightRegs_1 <= _zz_weightRegs_0;
              end
              if(_zz_2[2]) begin
                weightRegs_2 <= _zz_weightRegs_0;
              end
              if(_zz_2[3]) begin
                weightRegs_3 <= _zz_weightRegs_0;
              end
              if(_zz_2[4]) begin
                weightRegs_4 <= _zz_weightRegs_0;
              end
              if(_zz_2[5]) begin
                weightRegs_5 <= _zz_weightRegs_0;
              end
              if(_zz_2[6]) begin
                weightRegs_6 <= _zz_weightRegs_0;
              end
              if(_zz_2[7]) begin
                weightRegs_7 <= _zz_weightRegs_0;
              end
              if(_zz_2[8]) begin
                weightRegs_8 <= _zz_weightRegs_0;
              end
              if(_zz_2[9]) begin
                weightRegs_9 <= _zz_weightRegs_0;
              end
              if(_zz_2[10]) begin
                weightRegs_10 <= _zz_weightRegs_0;
              end
              if(_zz_2[11]) begin
                weightRegs_11 <= _zz_weightRegs_0;
              end
              if(_zz_2[12]) begin
                weightRegs_12 <= _zz_weightRegs_0;
              end
              if(_zz_2[13]) begin
                weightRegs_13 <= _zz_weightRegs_0;
              end
              if(_zz_2[14]) begin
                weightRegs_14 <= _zz_weightRegs_0;
              end
              if(_zz_2[15]) begin
                weightRegs_15 <= _zz_weightRegs_0;
              end
              if(_zz_2[16]) begin
                weightRegs_16 <= _zz_weightRegs_0;
              end
              if(_zz_2[17]) begin
                weightRegs_17 <= _zz_weightRegs_0;
              end
              if(_zz_2[18]) begin
                weightRegs_18 <= _zz_weightRegs_0;
              end
              if(_zz_2[19]) begin
                weightRegs_19 <= _zz_weightRegs_0;
              end
              if(_zz_2[20]) begin
                weightRegs_20 <= _zz_weightRegs_0;
              end
              if(_zz_2[21]) begin
                weightRegs_21 <= _zz_weightRegs_0;
              end
              if(_zz_2[22]) begin
                weightRegs_22 <= _zz_weightRegs_0;
              end
              if(_zz_2[23]) begin
                weightRegs_23 <= _zz_weightRegs_0;
              end
              if(_zz_2[24]) begin
                weightRegs_24 <= _zz_weightRegs_0;
              end
              if(_zz_2[25]) begin
                weightRegs_25 <= _zz_weightRegs_0;
              end
              if(_zz_2[26]) begin
                weightRegs_26 <= _zz_weightRegs_0;
              end
              if(_zz_2[27]) begin
                weightRegs_27 <= _zz_weightRegs_0;
              end
              if(_zz_2[28]) begin
                weightRegs_28 <= _zz_weightRegs_0;
              end
              if(_zz_2[29]) begin
                weightRegs_29 <= _zz_weightRegs_0;
              end
              if(_zz_2[30]) begin
                weightRegs_30 <= _zz_weightRegs_0;
              end
              if(_zz_2[31]) begin
                weightRegs_31 <= _zz_weightRegs_0;
              end
              if(_zz_2[32]) begin
                weightRegs_32 <= _zz_weightRegs_0;
              end
              if(_zz_2[33]) begin
                weightRegs_33 <= _zz_weightRegs_0;
              end
              if(_zz_2[34]) begin
                weightRegs_34 <= _zz_weightRegs_0;
              end
              if(_zz_2[35]) begin
                weightRegs_35 <= _zz_weightRegs_0;
              end
              if(_zz_2[36]) begin
                weightRegs_36 <= _zz_weightRegs_0;
              end
              if(_zz_2[37]) begin
                weightRegs_37 <= _zz_weightRegs_0;
              end
              if(_zz_2[38]) begin
                weightRegs_38 <= _zz_weightRegs_0;
              end
              if(_zz_2[39]) begin
                weightRegs_39 <= _zz_weightRegs_0;
              end
              if(_zz_2[40]) begin
                weightRegs_40 <= _zz_weightRegs_0;
              end
              if(_zz_2[41]) begin
                weightRegs_41 <= _zz_weightRegs_0;
              end
              if(_zz_2[42]) begin
                weightRegs_42 <= _zz_weightRegs_0;
              end
              if(_zz_2[43]) begin
                weightRegs_43 <= _zz_weightRegs_0;
              end
              if(_zz_2[44]) begin
                weightRegs_44 <= _zz_weightRegs_0;
              end
              if(_zz_2[45]) begin
                weightRegs_45 <= _zz_weightRegs_0;
              end
              if(_zz_2[46]) begin
                weightRegs_46 <= _zz_weightRegs_0;
              end
              if(_zz_2[47]) begin
                weightRegs_47 <= _zz_weightRegs_0;
              end
              if(_zz_2[48]) begin
                weightRegs_48 <= _zz_weightRegs_0;
              end
              if(_zz_2[49]) begin
                weightRegs_49 <= _zz_weightRegs_0;
              end
              if(_zz_2[50]) begin
                weightRegs_50 <= _zz_weightRegs_0;
              end
              if(_zz_2[51]) begin
                weightRegs_51 <= _zz_weightRegs_0;
              end
              if(_zz_2[52]) begin
                weightRegs_52 <= _zz_weightRegs_0;
              end
              if(_zz_2[53]) begin
                weightRegs_53 <= _zz_weightRegs_0;
              end
              if(_zz_2[54]) begin
                weightRegs_54 <= _zz_weightRegs_0;
              end
              if(_zz_2[55]) begin
                weightRegs_55 <= _zz_weightRegs_0;
              end
              if(_zz_2[56]) begin
                weightRegs_56 <= _zz_weightRegs_0;
              end
              if(_zz_2[57]) begin
                weightRegs_57 <= _zz_weightRegs_0;
              end
              if(_zz_2[58]) begin
                weightRegs_58 <= _zz_weightRegs_0;
              end
              if(_zz_2[59]) begin
                weightRegs_59 <= _zz_weightRegs_0;
              end
              if(_zz_2[60]) begin
                weightRegs_60 <= _zz_weightRegs_0;
              end
              if(_zz_2[61]) begin
                weightRegs_61 <= _zz_weightRegs_0;
              end
              if(_zz_2[62]) begin
                weightRegs_62 <= _zz_weightRegs_0;
              end
              if(_zz_2[63]) begin
                weightRegs_63 <= _zz_weightRegs_0;
              end
            end
          end
        end
      end
    end
  end


endmodule
