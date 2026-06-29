// Generator : SpinalHDL v1.14.2    git head : 78f29dc66110fc099a777992b6daa2f803ab445e
// Component : UartDecodeMatVecTop
// Git hash  : 237705502c61bdade8c30f703bb21970ecf91c07

`timescale 1ns/1ps 
module UartDecodeMatVecTop (
  input  wire          CLOCK_50,
  input  wire          UART_RXD,
  output wire          UART_TXD,
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

  wire       [3:0]    area_hex0_io_nibble;
  wire       [3:0]    area_hex1_io_nibble;
  wire       [3:0]    area_hex2_io_nibble;
  wire       [3:0]    area_hex3_io_nibble;
  reg        [3:0]    area_hex4_io_nibble;
  reg        [3:0]    area_hex5_io_nibble;
  wire                area_rx_io_valid;
  wire       [7:0]    area_rx_io_data;
  wire                area_rx_io_frameError;
  wire                area_tx_io_ready;
  wire                area_tx_io_txd;
  wire                area_tx_io_busy;
  wire                area_matVec_io_busy;
  wire                area_matVec_io_done;
  wire       [31:0]   area_matVec_io_outputs_0;
  wire       [31:0]   area_matVec_io_outputs_1;
  wire       [31:0]   area_matVec_io_outputs_2;
  wire       [31:0]   area_matVec_io_outputs_3;
  wire       [6:0]    area_hex0_io_segments;
  wire       [6:0]    area_hex1_io_segments;
  wire       [6:0]    area_hex2_io_segments;
  wire       [6:0]    area_hex3_io_segments;
  wire       [6:0]    area_hex4_io_segments;
  wire       [6:0]    area_hex5_io_segments;
  wire       [3:0]    _zz__zz_1;
  wire       [5:0]    _zz__zz_2;
  wire       [6:0]    _zz__zz_2_1;
  wire       [31:0]   _zz_area_responseByte;
  wire       [31:0]   _zz_area_responseByte_1;
  wire       [31:0]   _zz_area_responseByte_2;
  wire       [31:0]   _zz_area_responseByte_3;
  wire       [31:0]   _zz_area_responseByte_4;
  wire       [31:0]   _zz_area_responseByte_5;
  wire       [31:0]   _zz_area_responseByte_6;
  wire       [31:0]   _zz_area_responseByte_7;
  wire       [31:0]   _zz_area_responseByte_8;
  wire       [31:0]   _zz_area_responseByte_9;
  wire       [31:0]   _zz_area_responseByte_10;
  wire       [31:0]   _zz_area_responseByte_11;
  wire       [31:0]   _zz_area_responseByte_12;
  wire       [31:0]   _zz_area_responseByte_13;
  wire       [31:0]   _zz_area_responseByte_14;
  wire       [31:0]   _zz_area_responseByte_15;
  wire       [4:0]    _zz_when_UartDecodeMatVecTop_l186;
  wire       [4:0]    _zz_io_nibble;
  reg        [7:0]    area_activationRegs_0;
  reg        [7:0]    area_activationRegs_1;
  reg        [7:0]    area_activationRegs_2;
  reg        [7:0]    area_activationRegs_3;
  reg        [7:0]    area_activationRegs_4;
  reg        [7:0]    area_activationRegs_5;
  reg        [7:0]    area_activationRegs_6;
  reg        [7:0]    area_activationRegs_7;
  reg        [7:0]    area_activationRegs_8;
  reg        [7:0]    area_activationRegs_9;
  reg        [7:0]    area_activationRegs_10;
  reg        [7:0]    area_activationRegs_11;
  reg        [7:0]    area_activationRegs_12;
  reg        [7:0]    area_activationRegs_13;
  reg        [7:0]    area_activationRegs_14;
  reg        [7:0]    area_activationRegs_15;
  reg        [7:0]    area_weightRegs_0;
  reg        [7:0]    area_weightRegs_1;
  reg        [7:0]    area_weightRegs_2;
  reg        [7:0]    area_weightRegs_3;
  reg        [7:0]    area_weightRegs_4;
  reg        [7:0]    area_weightRegs_5;
  reg        [7:0]    area_weightRegs_6;
  reg        [7:0]    area_weightRegs_7;
  reg        [7:0]    area_weightRegs_8;
  reg        [7:0]    area_weightRegs_9;
  reg        [7:0]    area_weightRegs_10;
  reg        [7:0]    area_weightRegs_11;
  reg        [7:0]    area_weightRegs_12;
  reg        [7:0]    area_weightRegs_13;
  reg        [7:0]    area_weightRegs_14;
  reg        [7:0]    area_weightRegs_15;
  reg        [7:0]    area_weightRegs_16;
  reg        [7:0]    area_weightRegs_17;
  reg        [7:0]    area_weightRegs_18;
  reg        [7:0]    area_weightRegs_19;
  reg        [7:0]    area_weightRegs_20;
  reg        [7:0]    area_weightRegs_21;
  reg        [7:0]    area_weightRegs_22;
  reg        [7:0]    area_weightRegs_23;
  reg        [7:0]    area_weightRegs_24;
  reg        [7:0]    area_weightRegs_25;
  reg        [7:0]    area_weightRegs_26;
  reg        [7:0]    area_weightRegs_27;
  reg        [7:0]    area_weightRegs_28;
  reg        [7:0]    area_weightRegs_29;
  reg        [7:0]    area_weightRegs_30;
  reg        [7:0]    area_weightRegs_31;
  reg        [7:0]    area_weightRegs_32;
  reg        [7:0]    area_weightRegs_33;
  reg        [7:0]    area_weightRegs_34;
  reg        [7:0]    area_weightRegs_35;
  reg        [7:0]    area_weightRegs_36;
  reg        [7:0]    area_weightRegs_37;
  reg        [7:0]    area_weightRegs_38;
  reg        [7:0]    area_weightRegs_39;
  reg        [7:0]    area_weightRegs_40;
  reg        [7:0]    area_weightRegs_41;
  reg        [7:0]    area_weightRegs_42;
  reg        [7:0]    area_weightRegs_43;
  reg        [7:0]    area_weightRegs_44;
  reg        [7:0]    area_weightRegs_45;
  reg        [7:0]    area_weightRegs_46;
  reg        [7:0]    area_weightRegs_47;
  reg        [7:0]    area_weightRegs_48;
  reg        [7:0]    area_weightRegs_49;
  reg        [7:0]    area_weightRegs_50;
  reg        [7:0]    area_weightRegs_51;
  reg        [7:0]    area_weightRegs_52;
  reg        [7:0]    area_weightRegs_53;
  reg        [7:0]    area_weightRegs_54;
  reg        [7:0]    area_weightRegs_55;
  reg        [7:0]    area_weightRegs_56;
  reg        [7:0]    area_weightRegs_57;
  reg        [7:0]    area_weightRegs_58;
  reg        [7:0]    area_weightRegs_59;
  reg        [7:0]    area_weightRegs_60;
  reg        [7:0]    area_weightRegs_61;
  reg        [7:0]    area_weightRegs_62;
  reg        [7:0]    area_weightRegs_63;
  reg        [7:0]    area_cmdReg;
  reg        [7:0]    area_seqReg;
  reg        [15:0]   area_inDimReg;
  reg        [15:0]   area_outDimReg;
  reg        [31:0]   area_payloadLenReg;
  reg        [7:0]    area_statusReg;
  reg        [7:0]    area_responseCmdReg;
  reg        [3:0]    area_headerIndex;
  reg        [6:0]    area_payloadIndex;
  reg        [4:0]    area_txIndex;
  reg                 area_matVecStart;
  wire       [2:0]    area_idle;
  wire       [2:0]    area_header;
  wire       [2:0]    area_payload;
  wire       [2:0]    area_runCore;
  wire       [2:0]    area_sendResponse;
  reg        [2:0]    area_state;
  wire                when_UartDecodeMatVecTop_l81;
  wire                when_UartDecodeMatVecTop_l90;
  wire                when_UartDecodeMatVecTop_l108;
  wire                when_UartDecodeMatVecTop_l110;
  wire                when_UartDecodeMatVecTop_l112;
  wire                when_UartDecodeMatVecTop_l122;
  wire       [15:0]   _zz_1;
  wire       [7:0]    _zz_area_activationRegs_0;
  wire       [63:0]   _zz_2;
  wire       [7:0]    _zz_area_weightRegs_0;
  wire                when_UartDecodeMatVecTop_l128;
  wire                when_UartDecodeMatVecTop_l133;
  wire                when_UartDecodeMatVecTop_l146;
  reg        [7:0]    area_responseByte;
  wire       [4:0]    area_responseLength;
  reg                 area_txValidReg;
  reg        [7:0]    area_txDataReg;
  wire                when_UartDecodeMatVecTop_l183;
  wire                when_UartDecodeMatVecTop_l186;

  assign _zz__zz_1 = area_payloadIndex[3:0];
  assign _zz__zz_2_1 = (area_payloadIndex - 7'h10);
  assign _zz__zz_2 = _zz__zz_2_1[5:0];
  assign _zz_area_responseByte = area_matVec_io_outputs_0;
  assign _zz_area_responseByte_1 = area_matVec_io_outputs_0;
  assign _zz_area_responseByte_2 = area_matVec_io_outputs_0;
  assign _zz_area_responseByte_3 = area_matVec_io_outputs_0;
  assign _zz_area_responseByte_4 = area_matVec_io_outputs_1;
  assign _zz_area_responseByte_5 = area_matVec_io_outputs_1;
  assign _zz_area_responseByte_6 = area_matVec_io_outputs_1;
  assign _zz_area_responseByte_7 = area_matVec_io_outputs_1;
  assign _zz_area_responseByte_8 = area_matVec_io_outputs_2;
  assign _zz_area_responseByte_9 = area_matVec_io_outputs_2;
  assign _zz_area_responseByte_10 = area_matVec_io_outputs_2;
  assign _zz_area_responseByte_11 = area_matVec_io_outputs_2;
  assign _zz_area_responseByte_12 = area_matVec_io_outputs_3;
  assign _zz_area_responseByte_13 = area_matVec_io_outputs_3;
  assign _zz_area_responseByte_14 = area_matVec_io_outputs_3;
  assign _zz_area_responseByte_15 = area_matVec_io_outputs_3;
  assign _zz_when_UartDecodeMatVecTop_l186 = (area_responseLength - 5'h01);
  assign _zz_io_nibble = area_txIndex;
  UartRx area_rx (
    .io_rxd        (UART_RXD             ), //i
    .io_valid      (area_rx_io_valid     ), //o
    .io_data       (area_rx_io_data[7:0] ), //o
    .io_frameError (area_rx_io_frameError), //o
    .CLOCK_50      (CLOCK_50             )  //i
  );
  UartTx area_tx (
    .io_valid (area_txValidReg    ), //i
    .io_data  (area_txDataReg[7:0]), //i
    .io_ready (area_tx_io_ready   ), //o
    .io_txd   (area_tx_io_txd     ), //o
    .io_busy  (area_tx_io_busy    ), //o
    .CLOCK_50 (CLOCK_50           )  //i
  );
  DecodeMatVecInt8_i16_o4 area_matVec (
    .io_start         (area_matVecStart              ), //i
    .io_activation_0  (area_activationRegs_0[7:0]    ), //i
    .io_activation_1  (area_activationRegs_1[7:0]    ), //i
    .io_activation_2  (area_activationRegs_2[7:0]    ), //i
    .io_activation_3  (area_activationRegs_3[7:0]    ), //i
    .io_activation_4  (area_activationRegs_4[7:0]    ), //i
    .io_activation_5  (area_activationRegs_5[7:0]    ), //i
    .io_activation_6  (area_activationRegs_6[7:0]    ), //i
    .io_activation_7  (area_activationRegs_7[7:0]    ), //i
    .io_activation_8  (area_activationRegs_8[7:0]    ), //i
    .io_activation_9  (area_activationRegs_9[7:0]    ), //i
    .io_activation_10 (area_activationRegs_10[7:0]   ), //i
    .io_activation_11 (area_activationRegs_11[7:0]   ), //i
    .io_activation_12 (area_activationRegs_12[7:0]   ), //i
    .io_activation_13 (area_activationRegs_13[7:0]   ), //i
    .io_activation_14 (area_activationRegs_14[7:0]   ), //i
    .io_activation_15 (area_activationRegs_15[7:0]   ), //i
    .io_weights_0_0   (area_weightRegs_0[7:0]        ), //i
    .io_weights_0_1   (area_weightRegs_1[7:0]        ), //i
    .io_weights_0_2   (area_weightRegs_2[7:0]        ), //i
    .io_weights_0_3   (area_weightRegs_3[7:0]        ), //i
    .io_weights_0_4   (area_weightRegs_4[7:0]        ), //i
    .io_weights_0_5   (area_weightRegs_5[7:0]        ), //i
    .io_weights_0_6   (area_weightRegs_6[7:0]        ), //i
    .io_weights_0_7   (area_weightRegs_7[7:0]        ), //i
    .io_weights_0_8   (area_weightRegs_8[7:0]        ), //i
    .io_weights_0_9   (area_weightRegs_9[7:0]        ), //i
    .io_weights_0_10  (area_weightRegs_10[7:0]       ), //i
    .io_weights_0_11  (area_weightRegs_11[7:0]       ), //i
    .io_weights_0_12  (area_weightRegs_12[7:0]       ), //i
    .io_weights_0_13  (area_weightRegs_13[7:0]       ), //i
    .io_weights_0_14  (area_weightRegs_14[7:0]       ), //i
    .io_weights_0_15  (area_weightRegs_15[7:0]       ), //i
    .io_weights_1_0   (area_weightRegs_16[7:0]       ), //i
    .io_weights_1_1   (area_weightRegs_17[7:0]       ), //i
    .io_weights_1_2   (area_weightRegs_18[7:0]       ), //i
    .io_weights_1_3   (area_weightRegs_19[7:0]       ), //i
    .io_weights_1_4   (area_weightRegs_20[7:0]       ), //i
    .io_weights_1_5   (area_weightRegs_21[7:0]       ), //i
    .io_weights_1_6   (area_weightRegs_22[7:0]       ), //i
    .io_weights_1_7   (area_weightRegs_23[7:0]       ), //i
    .io_weights_1_8   (area_weightRegs_24[7:0]       ), //i
    .io_weights_1_9   (area_weightRegs_25[7:0]       ), //i
    .io_weights_1_10  (area_weightRegs_26[7:0]       ), //i
    .io_weights_1_11  (area_weightRegs_27[7:0]       ), //i
    .io_weights_1_12  (area_weightRegs_28[7:0]       ), //i
    .io_weights_1_13  (area_weightRegs_29[7:0]       ), //i
    .io_weights_1_14  (area_weightRegs_30[7:0]       ), //i
    .io_weights_1_15  (area_weightRegs_31[7:0]       ), //i
    .io_weights_2_0   (area_weightRegs_32[7:0]       ), //i
    .io_weights_2_1   (area_weightRegs_33[7:0]       ), //i
    .io_weights_2_2   (area_weightRegs_34[7:0]       ), //i
    .io_weights_2_3   (area_weightRegs_35[7:0]       ), //i
    .io_weights_2_4   (area_weightRegs_36[7:0]       ), //i
    .io_weights_2_5   (area_weightRegs_37[7:0]       ), //i
    .io_weights_2_6   (area_weightRegs_38[7:0]       ), //i
    .io_weights_2_7   (area_weightRegs_39[7:0]       ), //i
    .io_weights_2_8   (area_weightRegs_40[7:0]       ), //i
    .io_weights_2_9   (area_weightRegs_41[7:0]       ), //i
    .io_weights_2_10  (area_weightRegs_42[7:0]       ), //i
    .io_weights_2_11  (area_weightRegs_43[7:0]       ), //i
    .io_weights_2_12  (area_weightRegs_44[7:0]       ), //i
    .io_weights_2_13  (area_weightRegs_45[7:0]       ), //i
    .io_weights_2_14  (area_weightRegs_46[7:0]       ), //i
    .io_weights_2_15  (area_weightRegs_47[7:0]       ), //i
    .io_weights_3_0   (area_weightRegs_48[7:0]       ), //i
    .io_weights_3_1   (area_weightRegs_49[7:0]       ), //i
    .io_weights_3_2   (area_weightRegs_50[7:0]       ), //i
    .io_weights_3_3   (area_weightRegs_51[7:0]       ), //i
    .io_weights_3_4   (area_weightRegs_52[7:0]       ), //i
    .io_weights_3_5   (area_weightRegs_53[7:0]       ), //i
    .io_weights_3_6   (area_weightRegs_54[7:0]       ), //i
    .io_weights_3_7   (area_weightRegs_55[7:0]       ), //i
    .io_weights_3_8   (area_weightRegs_56[7:0]       ), //i
    .io_weights_3_9   (area_weightRegs_57[7:0]       ), //i
    .io_weights_3_10  (area_weightRegs_58[7:0]       ), //i
    .io_weights_3_11  (area_weightRegs_59[7:0]       ), //i
    .io_weights_3_12  (area_weightRegs_60[7:0]       ), //i
    .io_weights_3_13  (area_weightRegs_61[7:0]       ), //i
    .io_weights_3_14  (area_weightRegs_62[7:0]       ), //i
    .io_weights_3_15  (area_weightRegs_63[7:0]       ), //i
    .io_busy          (area_matVec_io_busy           ), //o
    .io_done          (area_matVec_io_done           ), //o
    .io_outputs_0     (area_matVec_io_outputs_0[31:0]), //o
    .io_outputs_1     (area_matVec_io_outputs_1[31:0]), //o
    .io_outputs_2     (area_matVec_io_outputs_2[31:0]), //o
    .io_outputs_3     (area_matVec_io_outputs_3[31:0]), //o
    .CLOCK_50         (CLOCK_50                      )  //i
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
  initial begin
    area_activationRegs_0 = 8'h0;
    area_activationRegs_1 = 8'h0;
    area_activationRegs_2 = 8'h0;
    area_activationRegs_3 = 8'h0;
    area_activationRegs_4 = 8'h0;
    area_activationRegs_5 = 8'h0;
    area_activationRegs_6 = 8'h0;
    area_activationRegs_7 = 8'h0;
    area_activationRegs_8 = 8'h0;
    area_activationRegs_9 = 8'h0;
    area_activationRegs_10 = 8'h0;
    area_activationRegs_11 = 8'h0;
    area_activationRegs_12 = 8'h0;
    area_activationRegs_13 = 8'h0;
    area_activationRegs_14 = 8'h0;
    area_activationRegs_15 = 8'h0;
    area_weightRegs_0 = 8'h0;
    area_weightRegs_1 = 8'h0;
    area_weightRegs_2 = 8'h0;
    area_weightRegs_3 = 8'h0;
    area_weightRegs_4 = 8'h0;
    area_weightRegs_5 = 8'h0;
    area_weightRegs_6 = 8'h0;
    area_weightRegs_7 = 8'h0;
    area_weightRegs_8 = 8'h0;
    area_weightRegs_9 = 8'h0;
    area_weightRegs_10 = 8'h0;
    area_weightRegs_11 = 8'h0;
    area_weightRegs_12 = 8'h0;
    area_weightRegs_13 = 8'h0;
    area_weightRegs_14 = 8'h0;
    area_weightRegs_15 = 8'h0;
    area_weightRegs_16 = 8'h0;
    area_weightRegs_17 = 8'h0;
    area_weightRegs_18 = 8'h0;
    area_weightRegs_19 = 8'h0;
    area_weightRegs_20 = 8'h0;
    area_weightRegs_21 = 8'h0;
    area_weightRegs_22 = 8'h0;
    area_weightRegs_23 = 8'h0;
    area_weightRegs_24 = 8'h0;
    area_weightRegs_25 = 8'h0;
    area_weightRegs_26 = 8'h0;
    area_weightRegs_27 = 8'h0;
    area_weightRegs_28 = 8'h0;
    area_weightRegs_29 = 8'h0;
    area_weightRegs_30 = 8'h0;
    area_weightRegs_31 = 8'h0;
    area_weightRegs_32 = 8'h0;
    area_weightRegs_33 = 8'h0;
    area_weightRegs_34 = 8'h0;
    area_weightRegs_35 = 8'h0;
    area_weightRegs_36 = 8'h0;
    area_weightRegs_37 = 8'h0;
    area_weightRegs_38 = 8'h0;
    area_weightRegs_39 = 8'h0;
    area_weightRegs_40 = 8'h0;
    area_weightRegs_41 = 8'h0;
    area_weightRegs_42 = 8'h0;
    area_weightRegs_43 = 8'h0;
    area_weightRegs_44 = 8'h0;
    area_weightRegs_45 = 8'h0;
    area_weightRegs_46 = 8'h0;
    area_weightRegs_47 = 8'h0;
    area_weightRegs_48 = 8'h0;
    area_weightRegs_49 = 8'h0;
    area_weightRegs_50 = 8'h0;
    area_weightRegs_51 = 8'h0;
    area_weightRegs_52 = 8'h0;
    area_weightRegs_53 = 8'h0;
    area_weightRegs_54 = 8'h0;
    area_weightRegs_55 = 8'h0;
    area_weightRegs_56 = 8'h0;
    area_weightRegs_57 = 8'h0;
    area_weightRegs_58 = 8'h0;
    area_weightRegs_59 = 8'h0;
    area_weightRegs_60 = 8'h0;
    area_weightRegs_61 = 8'h0;
    area_weightRegs_62 = 8'h0;
    area_weightRegs_63 = 8'h0;
    area_cmdReg = 8'h0;
    area_seqReg = 8'h0;
    area_inDimReg = 16'h0;
    area_outDimReg = 16'h0;
    area_payloadLenReg = 32'h0;
    area_statusReg = 8'h0;
    area_responseCmdReg = 8'h81;
    area_headerIndex = 4'b0000;
    area_payloadIndex = 7'h0;
    area_txIndex = 5'h0;
    area_matVecStart = 1'b0;
    area_state = 3'b000;
    area_txValidReg = 1'b0;
    area_txDataReg = 8'h0;
  end

  assign UART_TXD = area_tx_io_txd;
  assign area_idle = 3'b000;
  assign area_header = 3'b001;
  assign area_payload = 3'b010;
  assign area_runCore = 3'b011;
  assign area_sendResponse = 3'b100;
  assign when_UartDecodeMatVecTop_l81 = (area_rx_io_data == 8'ha5);
  assign when_UartDecodeMatVecTop_l90 = (area_rx_io_data == 8'h5a);
  assign when_UartDecodeMatVecTop_l108 = (area_cmdReg == 8'h01);
  assign when_UartDecodeMatVecTop_l110 = (area_cmdReg == 8'h02);
  assign when_UartDecodeMatVecTop_l112 = (area_cmdReg == 8'h10);
  assign when_UartDecodeMatVecTop_l122 = (area_payloadIndex < 7'h10);
  assign _zz_1 = ({15'd0,1'b1} <<< _zz__zz_1);
  assign _zz_area_activationRegs_0 = area_rx_io_data;
  assign _zz_2 = ({63'd0,1'b1} <<< _zz__zz_2);
  assign _zz_area_weightRegs_0 = area_rx_io_data;
  assign when_UartDecodeMatVecTop_l128 = (area_payloadIndex == 7'h4f);
  assign when_UartDecodeMatVecTop_l133 = (((area_inDimReg == 16'h0010) && (area_outDimReg == 16'h0004)) && (area_payloadLenReg == 32'h00000050));
  assign when_UartDecodeMatVecTop_l146 = ((area_state == area_runCore) && area_matVec_io_done);
  always @(*) begin
    area_responseByte = 8'h0;
    case(area_txIndex)
      5'h0 : begin
        area_responseByte = 8'h5a;
      end
      5'h01 : begin
        area_responseByte = 8'ha5;
      end
      5'h02 : begin
        area_responseByte = area_responseCmdReg;
      end
      5'h03 : begin
        area_responseByte = area_seqReg;
      end
      5'h04 : begin
        area_responseByte = area_statusReg;
      end
      5'h05 : begin
        area_responseByte = 8'h04;
      end
      5'h06 : begin
        area_responseByte = 8'h0;
      end
      5'h07 : begin
        area_responseByte = 8'h10;
      end
      5'h08 : begin
        area_responseByte = 8'h0;
      end
      5'h09 : begin
        area_responseByte = 8'h0;
      end
      5'h0a : begin
        area_responseByte = 8'h0;
      end
      default : begin
      end
    endcase
    case(area_txIndex)
      5'h0b : begin
        area_responseByte = _zz_area_responseByte[7 : 0];
      end
      default : begin
      end
    endcase
    case(area_txIndex)
      5'h0c : begin
        area_responseByte = _zz_area_responseByte_1[15 : 8];
      end
      default : begin
      end
    endcase
    case(area_txIndex)
      5'h0d : begin
        area_responseByte = _zz_area_responseByte_2[23 : 16];
      end
      default : begin
      end
    endcase
    case(area_txIndex)
      5'h0e : begin
        area_responseByte = _zz_area_responseByte_3[31 : 24];
      end
      default : begin
      end
    endcase
    case(area_txIndex)
      5'h0f : begin
        area_responseByte = _zz_area_responseByte_4[7 : 0];
      end
      default : begin
      end
    endcase
    case(area_txIndex)
      5'h10 : begin
        area_responseByte = _zz_area_responseByte_5[15 : 8];
      end
      default : begin
      end
    endcase
    case(area_txIndex)
      5'h11 : begin
        area_responseByte = _zz_area_responseByte_6[23 : 16];
      end
      default : begin
      end
    endcase
    case(area_txIndex)
      5'h12 : begin
        area_responseByte = _zz_area_responseByte_7[31 : 24];
      end
      default : begin
      end
    endcase
    case(area_txIndex)
      5'h13 : begin
        area_responseByte = _zz_area_responseByte_8[7 : 0];
      end
      default : begin
      end
    endcase
    case(area_txIndex)
      5'h14 : begin
        area_responseByte = _zz_area_responseByte_9[15 : 8];
      end
      default : begin
      end
    endcase
    case(area_txIndex)
      5'h15 : begin
        area_responseByte = _zz_area_responseByte_10[23 : 16];
      end
      default : begin
      end
    endcase
    case(area_txIndex)
      5'h16 : begin
        area_responseByte = _zz_area_responseByte_11[31 : 24];
      end
      default : begin
      end
    endcase
    case(area_txIndex)
      5'h17 : begin
        area_responseByte = _zz_area_responseByte_12[7 : 0];
      end
      default : begin
      end
    endcase
    case(area_txIndex)
      5'h18 : begin
        area_responseByte = _zz_area_responseByte_13[15 : 8];
      end
      default : begin
      end
    endcase
    case(area_txIndex)
      5'h19 : begin
        area_responseByte = _zz_area_responseByte_14[23 : 16];
      end
      default : begin
      end
    endcase
    case(area_txIndex)
      5'h1a : begin
        area_responseByte = _zz_area_responseByte_15[31 : 24];
      end
      default : begin
      end
    endcase
  end

  assign area_responseLength = 5'h1b;
  assign when_UartDecodeMatVecTop_l183 = ((area_state == area_sendResponse) && area_tx_io_ready);
  assign when_UartDecodeMatVecTop_l186 = (area_txIndex == _zz_when_UartDecodeMatVecTop_l186);
  assign area_hex0_io_nibble = area_statusReg[3 : 0];
  assign area_hex1_io_nibble = area_cmdReg[3 : 0];
  assign area_hex2_io_nibble = area_seqReg[3 : 0];
  assign area_hex3_io_nibble = _zz_io_nibble[3 : 0];
  always @(*) begin
    area_hex4_io_nibble = 4'b0000;
    area_hex4_io_nibble[0] = (area_state == area_sendResponse);
    area_hex4_io_nibble[1] = (area_state == area_runCore);
    area_hex4_io_nibble[2] = area_rx_io_frameError;
    area_hex4_io_nibble[3] = area_tx_io_busy;
  end

  always @(*) begin
    area_hex5_io_nibble = 4'b0000;
    area_hex5_io_nibble[0] = KEY[0];
    area_hex5_io_nibble[3 : 1] = SW[2 : 0];
  end

  assign HEX0 = area_hex0_io_segments;
  assign HEX1 = area_hex1_io_segments;
  assign HEX2 = area_hex2_io_segments;
  assign HEX3 = area_hex3_io_segments;
  assign HEX4 = area_hex4_io_segments;
  assign HEX5 = area_hex5_io_segments;
  always @(*) begin
    LEDR = 10'h0;
    LEDR[0] = (area_state == area_idle);
    LEDR[1] = (area_state == area_header);
    LEDR[2] = (area_state == area_payload);
    LEDR[3] = (area_state == area_runCore);
    LEDR[4] = (area_state == area_sendResponse);
    LEDR[5] = area_rx_io_valid;
    LEDR[6] = area_tx_io_busy;
    LEDR[7] = area_matVec_io_done;
    LEDR[9 : 8] = area_statusReg[1 : 0];
  end

  always @(posedge CLOCK_50) begin
    area_matVecStart <= 1'b0;
    if(area_rx_io_valid) begin
      if((area_state == area_idle)) begin
          if(when_UartDecodeMatVecTop_l81) begin
            area_headerIndex <= 4'b0001;
            area_payloadIndex <= 7'h0;
            area_state <= area_header;
          end
      end else if((area_state == area_header)) begin
          case(area_headerIndex)
            4'b0001 : begin
              if(when_UartDecodeMatVecTop_l90) begin
                area_headerIndex <= (area_headerIndex + 4'b0001);
              end else begin
                area_responseCmdReg <= 8'h81;
                area_statusReg <= 8'h01;
                area_txIndex <= 5'h0;
                area_state <= area_sendResponse;
              end
            end
            4'b0010 : begin
              area_cmdReg <= area_rx_io_data;
              area_headerIndex <= (area_headerIndex + 4'b0001);
            end
            4'b0011 : begin
              area_seqReg <= area_rx_io_data;
              area_headerIndex <= (area_headerIndex + 4'b0001);
            end
            4'b0100 : begin
              area_inDimReg[7 : 0] <= area_rx_io_data;
              area_headerIndex <= (area_headerIndex + 4'b0001);
            end
            4'b0101 : begin
              area_inDimReg[15 : 8] <= area_rx_io_data;
              area_headerIndex <= (area_headerIndex + 4'b0001);
            end
            4'b0110 : begin
              area_outDimReg[7 : 0] <= area_rx_io_data;
              area_headerIndex <= (area_headerIndex + 4'b0001);
            end
            4'b0111 : begin
              area_outDimReg[15 : 8] <= area_rx_io_data;
              area_headerIndex <= (area_headerIndex + 4'b0001);
            end
            4'b1000 : begin
              area_headerIndex <= (area_headerIndex + 4'b0001);
            end
            4'b1001 : begin
              area_payloadLenReg[7 : 0] <= area_rx_io_data;
              area_headerIndex <= (area_headerIndex + 4'b0001);
            end
            4'b1010 : begin
              area_payloadLenReg[15 : 8] <= area_rx_io_data;
              area_headerIndex <= (area_headerIndex + 4'b0001);
            end
            4'b1011 : begin
              area_payloadLenReg[23 : 16] <= area_rx_io_data;
              area_headerIndex <= (area_headerIndex + 4'b0001);
            end
            4'b1100 : begin
              area_payloadLenReg[31 : 24] <= area_rx_io_data;
              if(when_UartDecodeMatVecTop_l108) begin
                area_responseCmdReg <= 8'h81;
                area_statusReg <= 8'h0;
                area_txIndex <= 5'h0;
                area_state <= area_sendResponse;
              end else begin
                if(when_UartDecodeMatVecTop_l110) begin
                  area_responseCmdReg <= 8'h82;
                  area_statusReg <= 8'h0;
                  area_txIndex <= 5'h0;
                  area_state <= area_sendResponse;
                end else begin
                  if(when_UartDecodeMatVecTop_l112) begin
                    area_payloadIndex <= 7'h0;
                    area_state <= area_payload;
                  end else begin
                    area_responseCmdReg <= 8'h81;
                    area_statusReg <= 8'h03;
                    area_txIndex <= 5'h0;
                    area_state <= area_sendResponse;
                  end
                end
              end
            end
            default : begin
            end
          endcase
      end else if((area_state == area_payload)) begin
          if(when_UartDecodeMatVecTop_l122) begin
            if(_zz_1[0]) begin
              area_activationRegs_0 <= _zz_area_activationRegs_0;
            end
            if(_zz_1[1]) begin
              area_activationRegs_1 <= _zz_area_activationRegs_0;
            end
            if(_zz_1[2]) begin
              area_activationRegs_2 <= _zz_area_activationRegs_0;
            end
            if(_zz_1[3]) begin
              area_activationRegs_3 <= _zz_area_activationRegs_0;
            end
            if(_zz_1[4]) begin
              area_activationRegs_4 <= _zz_area_activationRegs_0;
            end
            if(_zz_1[5]) begin
              area_activationRegs_5 <= _zz_area_activationRegs_0;
            end
            if(_zz_1[6]) begin
              area_activationRegs_6 <= _zz_area_activationRegs_0;
            end
            if(_zz_1[7]) begin
              area_activationRegs_7 <= _zz_area_activationRegs_0;
            end
            if(_zz_1[8]) begin
              area_activationRegs_8 <= _zz_area_activationRegs_0;
            end
            if(_zz_1[9]) begin
              area_activationRegs_9 <= _zz_area_activationRegs_0;
            end
            if(_zz_1[10]) begin
              area_activationRegs_10 <= _zz_area_activationRegs_0;
            end
            if(_zz_1[11]) begin
              area_activationRegs_11 <= _zz_area_activationRegs_0;
            end
            if(_zz_1[12]) begin
              area_activationRegs_12 <= _zz_area_activationRegs_0;
            end
            if(_zz_1[13]) begin
              area_activationRegs_13 <= _zz_area_activationRegs_0;
            end
            if(_zz_1[14]) begin
              area_activationRegs_14 <= _zz_area_activationRegs_0;
            end
            if(_zz_1[15]) begin
              area_activationRegs_15 <= _zz_area_activationRegs_0;
            end
          end else begin
            if(_zz_2[0]) begin
              area_weightRegs_0 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[1]) begin
              area_weightRegs_1 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[2]) begin
              area_weightRegs_2 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[3]) begin
              area_weightRegs_3 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[4]) begin
              area_weightRegs_4 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[5]) begin
              area_weightRegs_5 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[6]) begin
              area_weightRegs_6 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[7]) begin
              area_weightRegs_7 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[8]) begin
              area_weightRegs_8 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[9]) begin
              area_weightRegs_9 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[10]) begin
              area_weightRegs_10 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[11]) begin
              area_weightRegs_11 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[12]) begin
              area_weightRegs_12 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[13]) begin
              area_weightRegs_13 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[14]) begin
              area_weightRegs_14 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[15]) begin
              area_weightRegs_15 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[16]) begin
              area_weightRegs_16 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[17]) begin
              area_weightRegs_17 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[18]) begin
              area_weightRegs_18 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[19]) begin
              area_weightRegs_19 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[20]) begin
              area_weightRegs_20 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[21]) begin
              area_weightRegs_21 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[22]) begin
              area_weightRegs_22 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[23]) begin
              area_weightRegs_23 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[24]) begin
              area_weightRegs_24 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[25]) begin
              area_weightRegs_25 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[26]) begin
              area_weightRegs_26 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[27]) begin
              area_weightRegs_27 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[28]) begin
              area_weightRegs_28 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[29]) begin
              area_weightRegs_29 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[30]) begin
              area_weightRegs_30 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[31]) begin
              area_weightRegs_31 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[32]) begin
              area_weightRegs_32 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[33]) begin
              area_weightRegs_33 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[34]) begin
              area_weightRegs_34 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[35]) begin
              area_weightRegs_35 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[36]) begin
              area_weightRegs_36 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[37]) begin
              area_weightRegs_37 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[38]) begin
              area_weightRegs_38 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[39]) begin
              area_weightRegs_39 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[40]) begin
              area_weightRegs_40 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[41]) begin
              area_weightRegs_41 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[42]) begin
              area_weightRegs_42 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[43]) begin
              area_weightRegs_43 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[44]) begin
              area_weightRegs_44 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[45]) begin
              area_weightRegs_45 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[46]) begin
              area_weightRegs_46 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[47]) begin
              area_weightRegs_47 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[48]) begin
              area_weightRegs_48 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[49]) begin
              area_weightRegs_49 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[50]) begin
              area_weightRegs_50 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[51]) begin
              area_weightRegs_51 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[52]) begin
              area_weightRegs_52 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[53]) begin
              area_weightRegs_53 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[54]) begin
              area_weightRegs_54 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[55]) begin
              area_weightRegs_55 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[56]) begin
              area_weightRegs_56 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[57]) begin
              area_weightRegs_57 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[58]) begin
              area_weightRegs_58 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[59]) begin
              area_weightRegs_59 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[60]) begin
              area_weightRegs_60 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[61]) begin
              area_weightRegs_61 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[62]) begin
              area_weightRegs_62 <= _zz_area_weightRegs_0;
            end
            if(_zz_2[63]) begin
              area_weightRegs_63 <= _zz_area_weightRegs_0;
            end
          end
          if(when_UartDecodeMatVecTop_l128) begin
            if(when_UartDecodeMatVecTop_l133) begin
              area_matVecStart <= 1'b1;
              area_state <= area_runCore;
            end else begin
              area_responseCmdReg <= 8'h90;
              area_statusReg <= 8'h02;
              area_txIndex <= 5'h0;
              area_state <= area_sendResponse;
            end
          end else begin
            area_payloadIndex <= (area_payloadIndex + 7'h01);
          end
      end
    end
    if(when_UartDecodeMatVecTop_l146) begin
      area_responseCmdReg <= 8'h90;
      area_statusReg <= 8'h0;
      area_txIndex <= 5'h0;
      area_state <= area_sendResponse;
    end
    area_txValidReg <= 1'b0;
    if(when_UartDecodeMatVecTop_l183) begin
      area_txDataReg <= area_responseByte;
      area_txValidReg <= 1'b1;
      if(when_UartDecodeMatVecTop_l186) begin
        area_state <= area_idle;
      end else begin
        area_txIndex <= (area_txIndex + 5'h01);
      end
    end
  end


endmodule
