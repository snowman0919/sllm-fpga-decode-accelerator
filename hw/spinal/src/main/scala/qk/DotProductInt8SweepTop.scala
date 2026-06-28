package qk

import spinal.core._

class DotProductInt8SweepTop(dim: Int) extends Component {
  noIoPrefix()

  val cfg = DotProductInt8Sweep.configForDim(dim)

  val io = new Bundle {
    val CLOCK_50 = in Bool ()
    val busy = out Bool ()
    val done = out Bool ()
    val score = out SInt (cfg.accWidth bits)
  }

  setDefinitionName(DotProductInt8Sweep.wrapperDefinitionName(dim))

  val coreClockDomain = ClockDomain(
    clock = io.CLOCK_50,
    config = ClockDomainConfig(resetKind = BOOT)
  )

  val area = new ClockingArea(coreClockDomain) {
    val dot = DotProductInt8Sweep.newNamedCore(dim)
    val (querySeed, keySeed) = DotProductInt8Stimulus.deterministicPair(dim)
    val bootTriggerPending = Reg(Bool()) init (True)

    for (idx <- 0 until cfg.dim) {
      dot.io.query(idx) := S(querySeed(idx), cfg.dataWidth bits)
      dot.io.key(idx) := S(keySeed(idx), cfg.dataWidth bits)
    }

    dot.io.start := bootTriggerPending

    when(bootTriggerPending) {
      bootTriggerPending := False
    }
  }

  io.busy := area.dot.io.busy
  io.done := area.dot.io.done
  io.score := area.dot.io.score
}
