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

object DotProductInt8Sweep {
  val SupportedDims: Seq[Int] = Seq(16, 32, 64, 128)

  def definitionName(dim: Int): String = s"DotProductInt8_dim$dim"

  def wrapperDefinitionName(dim: Int): String = s"DotProductInt8SweepTop_dim$dim"

  def configForDim(dim: Int): DotProductInt8Config = {
    require(SupportedDims.contains(dim), s"Unsupported dim=$dim. Supported dims: ${SupportedDims.mkString(", ")}")
    DotProductInt8Config(dim = dim, dataWidth = 8, accWidth = 32)
  }

  def newNamedCore(dim: Int): DotProductInt8 = dim match {
    case 16 => new DotProductInt8Dim16
    case 32 => new DotProductInt8Dim32
    case 64 => new DotProductInt8Dim64
    case 128 => new DotProductInt8Dim128
    case _ => throw new IllegalArgumentException(s"Unsupported dim=$dim")
  }
}

object DotProductInt8Stimulus {
  private val Dim16Query = Seq(-8, -7, -6, -5, -4, -3, -2, -1, 1, 2, 3, 4, 5, 6, 7, 8)
  private val Dim16Key = Seq(3, -1, 4, -2, 5, -3, 6, -4, 2, -5, 1, -6, 0, 7, -7, 8)

  private def clampInt8(value: Int): Int = value.max(-128).min(127)

  private def generatedQuery(dim: Int): Seq[Int] = {
    (0 until dim).map { idx =>
      val raw = ((idx * 5 + dim) % 17) - 8
      val adjusted = if (raw == 0) {
        if ((idx & 1) == 0) 8 else -8
      } else {
        raw
      }
      clampInt8(adjusted)
    }
  }

  private def generatedKey(dim: Int): Seq[Int] = {
    (0 until dim).map { idx =>
      val raw = ((idx * 7 + 3 + (dim / 16)) % 17) - 8
      val signed = if ((idx & 1) == 0) raw else -raw
      val adjusted = if (signed == 0) {
        if (((idx / 2) & 1) == 0) 7 else -7
      } else {
        signed
      }
      clampInt8(adjusted)
    }
  }

  def deterministicQuery(dim: Int): Seq[Int] = {
    require(dim > 0, "dim must be positive")
    if (dim == 16) Dim16Query else generatedQuery(dim)
  }

  def deterministicKey(dim: Int): Seq[Int] = {
    require(dim > 0, "dim must be positive")
    if (dim == 16) Dim16Key else generatedKey(dim)
  }

  def deterministicPair(dim: Int): (Seq[Int], Seq[Int]) = {
    val query = deterministicQuery(dim)
    val key = deterministicKey(dim)
    require(query.length == dim, s"query length mismatch for dim=$dim")
    require(key.length == dim, s"key length mismatch for dim=$dim")
    (query, key)
  }

  def expectedScore(dim: Int): Int = {
    val (query, key) = deterministicPair(dim)
    query.zip(key).map { case (q, k) => q * k }.sum
  }
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

class DotProductInt8Named(dim: Int) extends DotProductInt8(DotProductInt8Sweep.configForDim(dim)) {
  setDefinitionName(DotProductInt8Sweep.definitionName(dim))
}

class DotProductInt8Dim16 extends DotProductInt8Named(16)

class DotProductInt8Dim32 extends DotProductInt8Named(32)

class DotProductInt8Dim64 extends DotProductInt8Named(64)

class DotProductInt8Dim128 extends DotProductInt8Named(128)
