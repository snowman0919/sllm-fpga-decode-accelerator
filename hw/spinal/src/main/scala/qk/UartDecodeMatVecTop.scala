package qk

import spinal.core._

class UartDecodeMatVecTop(clockHz: Int = 50000000, baudRate: Int = 115200) extends Component {
  noIoPrefix()

  val io = new Bundle {
    val CLOCK_50 = in Bool ()
    val UART_RXD = in Bool ()
    val UART_TXD = out Bool ()
    val SW = in Bits (10 bits)
    val KEY = in Bits (2 bits)
    val LEDR = out Bits (10 bits)
    val HEX0 = out Bits (7 bits)
    val HEX1 = out Bits (7 bits)
    val HEX2 = out Bits (7 bits)
    val HEX3 = out Bits (7 bits)
    val HEX4 = out Bits (7 bits)
    val HEX5 = out Bits (7 bits)
  }

  val coreClockDomain = ClockDomain(
    clock = io.CLOCK_50,
    config = ClockDomainConfig(resetKind = BOOT)
  )

  val area = new ClockingArea(coreClockDomain) {
    val cfg = DecodeMatVecInt8.DemoConfig
    val rx = new UartRx(clockHz, baudRate)
    val tx = new UartTx(clockHz, baudRate)
    val matVec = new DecodeMatVecInt8Demo

    rx.io.rxd := io.UART_RXD
    io.UART_TXD := tx.io.txd

    val activationRegs = Vec(Reg(SInt(cfg.dataWidth bits)) init (0), cfg.inputDim)
    val weightRegs = Vec(Reg(SInt(cfg.dataWidth bits)) init (0), cfg.inputDim * cfg.outputDim)

    for (idx <- 0 until cfg.inputDim) {
      matVec.io.activation(idx) := activationRegs(idx)
    }
    for (row <- 0 until cfg.outputDim) {
      for (col <- 0 until cfg.inputDim) {
        matVec.io.weights(row)(col) := weightRegs(row * cfg.inputDim + col)
      }
    }

    val cmdReg = Reg(Bits(8 bits)) init (0)
    val seqReg = Reg(Bits(8 bits)) init (0)
    val inDimReg = Reg(Bits(16 bits)) init (0)
    val outDimReg = Reg(Bits(16 bits)) init (0)
    val payloadLenReg = Reg(Bits(32 bits)) init (0)
    val statusReg = Reg(Bits(8 bits)) init (UartPacketProtocol.StatusOk)
    val responseCmdReg = Reg(Bits(8 bits)) init (UartPacketProtocol.RspPingAck)

    val headerIndex = Reg(UInt(4 bits)) init (0)
    val payloadIndex = Reg(UInt(7 bits)) init (0)
    val txIndex = Reg(UInt(5 bits)) init (0)
    val matVecStart = Reg(Bool()) init (False)
    matVec.io.start := matVecStart
    matVecStart := False

    val idle = U(0, 3 bits)
    val header = U(1, 3 bits)
    val payload = U(2, 3 bits)
    val runCore = U(3, 3 bits)
    val sendResponse = U(4, 3 bits)
    val state = Reg(UInt(3 bits)) init (0)

    def prepareResponse(responseCmd: Int, status: Int): Unit = {
      responseCmdReg := B(responseCmd, 8 bits)
      statusReg := B(status, 8 bits)
      txIndex := 0
      state := sendResponse
    }

    when(rx.io.valid) {
      switch(state) {
        is(idle) {
          when(rx.io.data === B(UartPacketProtocol.ReqMagic0, 8 bits)) {
            headerIndex := 1
            payloadIndex := 0
            state := header
          }
        }
        is(header) {
          switch(headerIndex) {
            is(1) {
              when(rx.io.data === B(UartPacketProtocol.ReqMagic1, 8 bits)) {
                headerIndex := headerIndex + 1
              } otherwise {
                prepareResponse(UartPacketProtocol.RspPingAck, UartPacketProtocol.StatusBadPacket)
              }
            }
            is(2) { cmdReg := rx.io.data; headerIndex := headerIndex + 1 }
            is(3) { seqReg := rx.io.data; headerIndex := headerIndex + 1 }
            is(4) { inDimReg(7 downto 0) := rx.io.data; headerIndex := headerIndex + 1 }
            is(5) { inDimReg(15 downto 8) := rx.io.data; headerIndex := headerIndex + 1 }
            is(6) { outDimReg(7 downto 0) := rx.io.data; headerIndex := headerIndex + 1 }
            is(7) { outDimReg(15 downto 8) := rx.io.data; headerIndex := headerIndex + 1 }
            is(8) { headerIndex := headerIndex + 1 }
            is(9) { payloadLenReg(7 downto 0) := rx.io.data; headerIndex := headerIndex + 1 }
            is(10) { payloadLenReg(15 downto 8) := rx.io.data; headerIndex := headerIndex + 1 }
            is(11) { payloadLenReg(23 downto 16) := rx.io.data; headerIndex := headerIndex + 1 }
            is(12) {
              payloadLenReg(31 downto 24) := rx.io.data
              when(cmdReg === B(UartPacketProtocol.CmdPing, 8 bits)) {
                prepareResponse(UartPacketProtocol.RspPingAck, UartPacketProtocol.StatusOk)
              } elsewhen (cmdReg === B(UartPacketProtocol.CmdReset, 8 bits)) {
                prepareResponse(UartPacketProtocol.RspResetAck, UartPacketProtocol.StatusOk)
              } elsewhen (cmdReg === B(UartPacketProtocol.CmdMatVec, 8 bits)) {
                payloadIndex := 0
                state := payload
              } otherwise {
                prepareResponse(UartPacketProtocol.RspPingAck, UartPacketProtocol.StatusBadCommand)
              }
            }
          }
        }
        is(payload) {
          when(payloadIndex < U(cfg.inputDim, 7 bits)) {
            activationRegs(payloadIndex.resized) := rx.io.data.asSInt
          } otherwise {
            weightRegs((payloadIndex - U(cfg.inputDim, 7 bits)).resized) := rx.io.data.asSInt
          }

          when(payloadIndex === U((cfg.inputDim * cfg.outputDim + cfg.inputDim) - 1, 7 bits)) {
            when(
              inDimReg.asUInt === U(cfg.inputDim, 16 bits) &&
                outDimReg.asUInt === U(cfg.outputDim, 16 bits) &&
                payloadLenReg.asUInt === U(cfg.inputDim * cfg.outputDim + cfg.inputDim, 32 bits)
            ) {
              matVecStart := True
              state := runCore
            } otherwise {
              prepareResponse(UartPacketProtocol.RspMatVecResult, UartPacketProtocol.StatusBadShape)
            }
          } otherwise {
            payloadIndex := payloadIndex + 1
          }
        }
      }
    }

    when(state === runCore && matVec.io.done) {
      prepareResponse(UartPacketProtocol.RspMatVecResult, UartPacketProtocol.StatusOk)
    }

    val responseByte = Bits(8 bits)
    responseByte := B(0, 8 bits)
    switch(txIndex) {
      is(0) { responseByte := B(UartPacketProtocol.RespMagic0, 8 bits) }
      is(1) { responseByte := B(UartPacketProtocol.RespMagic1, 8 bits) }
      is(2) { responseByte := responseCmdReg }
      is(3) { responseByte := seqReg }
      is(4) { responseByte := statusReg }
      is(5) { responseByte := B(cfg.outputDim & 0xff, 8 bits) }
      is(6) { responseByte := B((cfg.outputDim >> 8) & 0xff, 8 bits) }
      is(7) { responseByte := B((cfg.outputDim * 4) & 0xff, 8 bits) }
      is(8) { responseByte := B(((cfg.outputDim * 4) >> 8) & 0xff, 8 bits) }
      is(9) { responseByte := B(0, 8 bits) }
      is(10) { responseByte := B(0, 8 bits) }
    }
    for (row <- 0 until cfg.outputDim) {
      for (byte <- 0 until 4) {
        val idx = 11 + row * 4 + byte
        switch(txIndex) {
          is(idx) {
            responseByte := matVec.io.outputs(row).asBits((byte * 8 + 7) downto (byte * 8))
          }
        }
      }
    }

    val responseLength = U(11 + cfg.outputDim * 4, 5 bits)
    val txValidReg = Reg(Bool()) init (False)
    val txDataReg = Reg(Bits(8 bits)) init (0)
    tx.io.valid := txValidReg
    tx.io.data := txDataReg
    txValidReg := False

    when(state === sendResponse && tx.io.ready) {
      txDataReg := responseByte
      txValidReg := True
      when(txIndex === responseLength - 1) {
        state := idle
      } otherwise {
        txIndex := txIndex + 1
      }
    }

    val hex0 = new HexDisplay
    val hex1 = new HexDisplay
    val hex2 = new HexDisplay
    val hex3 = new HexDisplay
    val hex4 = new HexDisplay
    val hex5 = new HexDisplay

    hex0.io.nibble := statusReg(3 downto 0)
    hex1.io.nibble := cmdReg(3 downto 0)
    hex2.io.nibble := seqReg(3 downto 0)
    hex3.io.nibble := txIndex.asBits(3 downto 0)
    hex4.io.nibble := B(0, 4 bits)
    hex4.io.nibble(0) := state === sendResponse
    hex4.io.nibble(1) := state === runCore
    hex4.io.nibble(2) := rx.io.frameError
    hex4.io.nibble(3) := tx.io.busy
    hex5.io.nibble := B(0, 4 bits)
    hex5.io.nibble(0) := io.KEY(0)
    hex5.io.nibble(3 downto 1) := io.SW(2 downto 0)

    io.HEX0 := hex0.io.segments
    io.HEX1 := hex1.io.segments
    io.HEX2 := hex2.io.segments
    io.HEX3 := hex3.io.segments
    io.HEX4 := hex4.io.segments
    io.HEX5 := hex5.io.segments

    io.LEDR := B(0, 10 bits)
    io.LEDR(0) := state === idle
    io.LEDR(1) := state === header
    io.LEDR(2) := state === payload
    io.LEDR(3) := state === runCore
    io.LEDR(4) := state === sendResponse
    io.LEDR(5) := rx.io.valid
    io.LEDR(6) := tx.io.busy
    io.LEDR(7) := matVec.io.done
    io.LEDR(9 downto 8) := statusReg(1 downto 0)
  }
}
