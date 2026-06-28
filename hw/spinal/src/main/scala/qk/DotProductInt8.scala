package qk

import spinal.core._

case class DotProductInt8Config(
    dim: Int = 16,
    dataWidth: Int = 8,
    accWidth: Int = 32
) {
  require(dim > 0, "dim must be positive")
  require(dataWidth > 0, "dataWidth must be positive")
  require(accWidth >= (dataWidth * 2), "accWidth should safely hold a single product")
}

class DotProductInt8(cfg: DotProductInt8Config = DotProductInt8Config()) extends Component {
  val io = new Bundle {
    val start = in Bool ()
    val query = in Vec(SInt(cfg.dataWidth bits), cfg.dim)
    val key = in Vec(SInt(cfg.dataWidth bits), cfg.dim)
    val busy = out Bool ()
    val done = out Bool ()
    val score = out SInt (cfg.accWidth bits)
  }

  private val indexWidth = Math.max(log2Up(cfg.dim), 1)
  private val lastIndex = U(cfg.dim - 1, indexWidth bits)

  val busyReg = Reg(Bool()) init (False)
  val doneReg = Reg(Bool()) init (False)
  val indexReg = Reg(UInt(indexWidth bits)) init (0)
  val accReg = Reg(SInt(cfg.accWidth bits)) init (0)
  val scoreReg = Reg(SInt(cfg.accWidth bits)) init (0)

  io.busy := busyReg
  io.done := doneReg
  io.score := scoreReg

  doneReg := False

  when(io.start && !busyReg) {
    busyReg := True
    indexReg := 0
    accReg := 0
    scoreReg := 0
  } elsewhen (busyReg) {
    val product = (io.query(indexReg) * io.key(indexReg)).resize(cfg.accWidth)
    val nextAcc = (accReg + product).resize(cfg.accWidth)

    accReg := nextAcc

    when(indexReg === lastIndex) {
      busyReg := False
      doneReg := True
      scoreReg := nextAcc
    } otherwise {
      indexReg := indexReg + 1
    }
  }
}

class DotProductInt8Dim16 extends DotProductInt8(DotProductInt8Config(dim = 16, dataWidth = 8, accWidth = 32)) {
  setDefinitionName("DotProductInt8_dim16")
}
