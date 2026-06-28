package qk

import spinal.core._

class De10LiteTop extends Component {
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
    val cfg = DotProductInt8Config()
    val dot = new DotProductInt8Dim16

    val querySeed = Seq(-8, -7, -6, -5, -4, -3, -2, -1, 1, 2, 3, 4, 5, 6, 7, 8)
    val keySeed = Seq(3, -1, 4, -2, 5, -3, 6, -4, 2, -5, 1, -6, 0, 7, -7, 8)

    assert(querySeed.length == cfg.dim)
    assert(keySeed.length == cfg.dim)

    for (idx <- 0 until cfg.dim) {
      dot.io.query(idx) := S(querySeed(idx), cfg.dataWidth bits)
      dot.io.key(idx) := S(keySeed(idx), cfg.dataWidth bits)
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

    dot.io.start := startPulse

    val scoreBits = dot.io.score.asBits
    val signBit = scoreBits(cfg.accWidth - 1)

    val statusNibble = Bits(4 bits)
    statusNibble(0) := dot.io.done
    statusNibble(1) := dot.io.busy
    statusNibble(2) := signBit
    statusNibble(3) := rerunCounter(0)

    val hex0 = new HexDisplay
    val hex1 = new HexDisplay
    val hex2 = new HexDisplay
    val hex3 = new HexDisplay
    val hex4 = new HexDisplay
    val hex5 = new HexDisplay

    hex0.io.nibble := scoreBits(3 downto 0)
    hex1.io.nibble := scoreBits(7 downto 4)
    hex2.io.nibble := scoreBits(11 downto 8)
    hex3.io.nibble := scoreBits(15 downto 12)
    hex4.io.nibble := statusNibble
    hex5.io.nibble := rerunCounter.asBits

    io.HEX0 := hex0.io.segments
    io.HEX1 := hex1.io.segments
    io.HEX2 := hex2.io.segments
    io.HEX3 := hex3.io.segments
    io.HEX4 := hex4.io.segments
    io.HEX5 := hex5.io.segments

    io.LEDR := B(0, 10 bits)
    io.LEDR(0) := dot.io.done
    io.LEDR(1) := dot.io.busy
    io.LEDR(2) := signBit
    io.LEDR(3) := io.SW(0)
    io.LEDR(4) := io.KEY(0)
    io.LEDR(9 downto 5) := scoreBits(4 downto 0)
  }
}
