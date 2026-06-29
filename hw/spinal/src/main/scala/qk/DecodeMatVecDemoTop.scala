package qk

import spinal.core._

class DecodeMatVecDemoTop extends Component {
  noIoPrefix()

  val io = new Bundle {
    val CLOCK_50 = in Bool ()
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
    val matVec = new DecodeMatVecInt8Demo
    val activation = DecodeMatVecInt8Stimulus.deterministicActivation(cfg.inputDim)
    val weights = DecodeMatVecInt8Stimulus.deterministicWeights(cfg)

    for (idx <- 0 until cfg.inputDim) {
      matVec.io.activation(idx) := S(activation(idx), cfg.dataWidth bits)
    }

    for (row <- 0 until cfg.outputDim) {
      for (col <- 0 until cfg.inputDim) {
        matVec.io.weights(row)(col) := S(weights(row)(col), cfg.dataWidth bits)
      }
    }

    val swPrev = RegNext(io.SW(0)) init (False)
    val keyPrev = RegNext(io.KEY(0)) init (False)
    val bootTriggerPending = Reg(Bool()) init (True)
    val rerunCounter = Reg(UInt(4 bits)) init (0)

    val swToggle = io.SW(0) =/= swPrev
    val keyToggle = io.KEY(0) =/= keyPrev
    val startPulse = Bool()
    startPulse := False

    when(bootTriggerPending) {
      startPulse := True
      bootTriggerPending := False
    } elsewhen (swToggle || keyToggle) {
      startPulse := True
      rerunCounter := rerunCounter + 1
    }

    matVec.io.start := startPulse

    val outputIndex = io.SW(2 downto 1).asUInt.resize(log2Up(cfg.outputDim) bits)
    val selectedOutput = matVec.io.outputs(outputIndex)
    val selectedBits = selectedOutput.asBits
    val signBit = selectedBits(cfg.accWidth - 1)

    val statusNibble = Bits(4 bits)
    statusNibble(0) := matVec.io.done
    statusNibble(1) := matVec.io.busy
    statusNibble(2) := signBit
    statusNibble(3) := rerunCounter(0)

    val hex0 = new HexDisplay
    val hex1 = new HexDisplay
    val hex2 = new HexDisplay
    val hex3 = new HexDisplay
    val hex4 = new HexDisplay
    val hex5 = new HexDisplay

    hex0.io.nibble := selectedBits(3 downto 0)
    hex1.io.nibble := selectedBits(7 downto 4)
    hex2.io.nibble := selectedBits(11 downto 8)
    hex3.io.nibble := selectedBits(15 downto 12)
    hex4.io.nibble := statusNibble
    hex5.io.nibble := rerunCounter.asBits

    io.HEX0 := hex0.io.segments
    io.HEX1 := hex1.io.segments
    io.HEX2 := hex2.io.segments
    io.HEX3 := hex3.io.segments
    io.HEX4 := hex4.io.segments
    io.HEX5 := hex5.io.segments

    io.LEDR := B(0, 10 bits)
    io.LEDR(0) := matVec.io.done
    io.LEDR(1) := matVec.io.busy
    io.LEDR(2) := signBit
    io.LEDR(4 downto 3) := outputIndex.asBits
    io.LEDR(8 downto 5) := selectedBits(3 downto 0)
    io.LEDR(9) := io.SW(0)
  }
}
