package qk

import spinal.core._

case class DecodeMatVecInt8Config(
    inputDim: Int = 16,
    outputDim: Int = 4,
    tileDim: Int = 1,
    dataWidth: Int = 8,
    accWidth: Int = 32
) {
  require(inputDim > 0, "inputDim must be positive")
  require(outputDim > 0, "outputDim must be positive")
  require(tileDim == 1, "current primitive validates the sequential tileDim=1 mode")
  require(dataWidth > 0, "dataWidth must be positive")
  require(accWidth >= (dataWidth * 2), "accWidth should safely hold a single product")
}

object DecodeMatVecInt8 {
  val DemoConfig: DecodeMatVecInt8Config = DecodeMatVecInt8Config(inputDim = 16, outputDim = 4)

  def definitionName(cfg: DecodeMatVecInt8Config): String =
    s"DecodeMatVecInt8_i${cfg.inputDim}_o${cfg.outputDim}"
}

object DecodeMatVecInt8Stimulus {
  private def clampInt8(value: Int): Int = value.max(-128).min(127)

  def deterministicActivation(inputDim: Int): Seq[Int] = {
    require(inputDim > 0, "inputDim must be positive")
    (0 until inputDim).map { idx =>
      val raw = ((idx * 9 + 5) % 31) - 15
      val adjusted = if (raw == 0) {
        if ((idx & 1) == 0) 11 else -11
      } else {
        raw
      }
      clampInt8(adjusted)
    }
  }

  def deterministicWeight(outputIndex: Int, inputIndex: Int): Int = {
    val raw = ((outputIndex + 3) * (inputIndex + 5) + outputIndex * 7) % 29
    val signed = raw - 14
    val adjusted = if (((outputIndex + inputIndex) & 1) == 0) signed else -signed
    clampInt8(if (adjusted == 0) outputIndex - inputIndex else adjusted)
  }

  def deterministicWeights(cfg: DecodeMatVecInt8Config): Seq[Seq[Int]] = {
    (0 until cfg.outputDim).map { row =>
      (0 until cfg.inputDim).map { col =>
        deterministicWeight(row, col)
      }
    }
  }

  def expectedOutputs(cfg: DecodeMatVecInt8Config): Seq[Int] = {
    val activation = deterministicActivation(cfg.inputDim)
    val weights = deterministicWeights(cfg)
    weights.map { row =>
      activation.zip(row).map { case (a, w) => a * w }.sum
    }
  }
}

class DecodeMatVecInt8(cfg: DecodeMatVecInt8Config = DecodeMatVecInt8.DemoConfig) extends Component {
  val io = new Bundle {
    val start = in Bool ()
    val activation = in Vec(SInt(cfg.dataWidth bits), cfg.inputDim)
    val weights = in Vec(Vec(SInt(cfg.dataWidth bits), cfg.inputDim), cfg.outputDim)
    val busy = out Bool ()
    val done = out Bool ()
    val outputs = out Vec(SInt(cfg.accWidth bits), cfg.outputDim)
  }

  private val inputIndexWidth = Math.max(log2Up(cfg.inputDim), 1)
  private val outputIndexWidth = Math.max(log2Up(cfg.outputDim), 1)
  private val lastInputIndex = U(cfg.inputDim - 1, inputIndexWidth bits)
  private val lastOutputIndex = U(cfg.outputDim - 1, outputIndexWidth bits)

  val busyReg = Reg(Bool()) init (False)
  val doneReg = Reg(Bool()) init (False)
  val inputIndexReg = Reg(UInt(inputIndexWidth bits)) init (0)
  val outputIndexReg = Reg(UInt(outputIndexWidth bits)) init (0)
  val accReg = Reg(SInt(cfg.accWidth bits)) init (0)
  val outputRegs = Vec(Reg(SInt(cfg.accWidth bits)) init (0), cfg.outputDim)

  io.busy := busyReg
  io.done := doneReg
  io.outputs := outputRegs

  doneReg := False

  when(io.start && !busyReg) {
    busyReg := True
    inputIndexReg := 0
    outputIndexReg := 0
    accReg := 0
    for (idx <- 0 until cfg.outputDim) {
      outputRegs(idx) := 0
    }
  } elsewhen (busyReg) {
    val product = (io.activation(inputIndexReg) * io.weights(outputIndexReg)(inputIndexReg)).resize(cfg.accWidth)
    val nextAcc = (accReg + product).resize(cfg.accWidth)

    when(inputIndexReg === lastInputIndex) {
      outputRegs(outputIndexReg) := nextAcc
      accReg := 0
      inputIndexReg := 0

      when(outputIndexReg === lastOutputIndex) {
        busyReg := False
        doneReg := True
      } otherwise {
        outputIndexReg := outputIndexReg + 1
      }
    } otherwise {
      accReg := nextAcc
      inputIndexReg := inputIndexReg + 1
    }
  }
}

class DecodeMatVecInt8Demo extends DecodeMatVecInt8(DecodeMatVecInt8.DemoConfig) {
  setDefinitionName(DecodeMatVecInt8.definitionName(DecodeMatVecInt8.DemoConfig))
}
