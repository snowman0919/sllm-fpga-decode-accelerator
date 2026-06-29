package qk

import spinal.core._

object DecodeMatVecRegMap {
  val Control = 0x000
  val Status = 0x004
  val Config = 0x008
  val Seq = 0x010
  val ActivationBase = 0x100
  val WeightBase = 0x200
  val ResultBase = 0x300

  val ActivationWords = DecodeMatVecInt8.DemoConfig.inputDim
  val WeightWords = DecodeMatVecInt8.DemoConfig.inputDim * DecodeMatVecInt8.DemoConfig.outputDim
  val ResultWords = DecodeMatVecInt8.DemoConfig.outputDim
}

class DecodeMatVecRegBank(cfg: DecodeMatVecInt8Config = DecodeMatVecInt8.DemoConfig) extends Component {
  val io = new Bundle {
    val address = in UInt (12 bits)
    val read = in Bool ()
    val write = in Bool ()
    val writedata = in Bits (32 bits)
    val readdata = out Bits (32 bits)
    val waitrequest = out Bool ()
    val readdatavalid = out Bool ()
    val debugStatus = out Bits (8 bits)
    val debugSeq = out Bits (8 bits)
  }

  private val activationWordBase = DecodeMatVecRegMap.ActivationBase / 4
  private val weightWordBase = DecodeMatVecRegMap.WeightBase / 4
  private val resultWordBase = DecodeMatVecRegMap.ResultBase / 4

  val matVec = new DecodeMatVecInt8Demo
  val activationRegs = Vec(Reg(SInt(cfg.dataWidth bits)) init (0), cfg.inputDim)
  val weightRegs = Vec(Reg(SInt(cfg.dataWidth bits)) init (0), cfg.inputDim * cfg.outputDim)
  val doneLatched = Reg(Bool()) init (False)
  val errorReg = Reg(Bool()) init (False)
  val seqReg = Reg(Bits(32 bits)) init (0)
  val startPulse = Reg(Bool()) init (False)

  startPulse := False
  matVec.io.start := startPulse

  for (idx <- 0 until cfg.inputDim) {
    matVec.io.activation(idx) := activationRegs(idx)
  }
  for (row <- 0 until cfg.outputDim) {
    for (col <- 0 until cfg.inputDim) {
      matVec.io.weights(row)(col) := weightRegs(row * cfg.inputDim + col)
    }
  }

  when(matVec.io.done) {
    doneLatched := True
  }

  io.waitrequest := False
  io.readdatavalid := RegNext(io.read) init (False)
  io.debugSeq := seqReg(7 downto 0)
  io.debugStatus := B(0, 8 bits)
  io.debugStatus(0) := matVec.io.busy
  io.debugStatus(1) := doneLatched
  io.debugStatus(2) := errorReg

  val wordAddress = io.address(11 downto 2)
  val readData = Bits(32 bits)
  readData := B(0, 32 bits)

  when(wordAddress === U(DecodeMatVecRegMap.Status / 4, 10 bits)) {
    readData(0) := matVec.io.busy
    readData(1) := doneLatched
    readData(2) := errorReg
  } elsewhen (wordAddress === U(DecodeMatVecRegMap.Config / 4, 10 bits)) {
    readData := B((cfg.outputDim << 16) | cfg.inputDim, 32 bits)
  } elsewhen (wordAddress === U(DecodeMatVecRegMap.Seq / 4, 10 bits)) {
    readData := seqReg
  } elsewhen (
    wordAddress >= U(activationWordBase, 10 bits) &&
      wordAddress < U(activationWordBase + cfg.inputDim, 10 bits)
  ) {
    val idx = (wordAddress - U(activationWordBase, 10 bits)).resized
    readData(7 downto 0) := activationRegs(idx).asBits
  } elsewhen (
    wordAddress >= U(weightWordBase, 10 bits) &&
      wordAddress < U(weightWordBase + cfg.inputDim * cfg.outputDim, 10 bits)
  ) {
    val idx = (wordAddress - U(weightWordBase, 10 bits)).resized
    readData(7 downto 0) := weightRegs(idx).asBits
  } elsewhen (
    wordAddress >= U(resultWordBase, 10 bits) &&
      wordAddress < U(resultWordBase + cfg.outputDim, 10 bits)
  ) {
    val idx = (wordAddress - U(resultWordBase, 10 bits)).resized
    readData := matVec.io.outputs(idx).asBits
  }
  io.readdata := readData

  when(io.write) {
    when(wordAddress === U(DecodeMatVecRegMap.Control / 4, 10 bits)) {
      when(io.writedata(1)) {
        doneLatched := False
        errorReg := False
      }
      when(io.writedata(2)) {
        doneLatched := False
      }
      when(io.writedata(0)) {
        when(matVec.io.busy) {
          errorReg := True
        } otherwise {
          doneLatched := False
          errorReg := False
          startPulse := True
        }
      }
    } elsewhen (wordAddress === U(DecodeMatVecRegMap.Seq / 4, 10 bits)) {
      seqReg := io.writedata
    } elsewhen (
      wordAddress >= U(activationWordBase, 10 bits) &&
        wordAddress < U(activationWordBase + cfg.inputDim, 10 bits)
    ) {
      val idx = (wordAddress - U(activationWordBase, 10 bits)).resized
      activationRegs(idx) := io.writedata(7 downto 0).asSInt
    } elsewhen (
      wordAddress >= U(weightWordBase, 10 bits) &&
        wordAddress < U(weightWordBase + cfg.inputDim * cfg.outputDim, 10 bits)
    ) {
      val idx = (wordAddress - U(weightWordBase, 10 bits)).resized
      weightRegs(idx) := io.writedata(7 downto 0).asSInt
    }
  }
}
