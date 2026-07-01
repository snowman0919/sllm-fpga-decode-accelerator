package qk

import java.io.File
import java.io.PrintWriter

import org.scalatest.funsuite.AnyFunSuite
import spinal.core.sim._
import spinal.sim._

class DecodeMatVecInt8Sim extends AnyFunSuite {
  private def runCoreSimulation(cfg: DecodeMatVecInt8Config): (Seq[Int], Int) = {
    val activation = DecodeMatVecInt8Stimulus.deterministicActivation(cfg.inputDim)
    val weights = DecodeMatVecInt8Stimulus.deterministicWeights(cfg)
    val expected = DecodeMatVecInt8Stimulus.expectedOutputs(cfg)
    var observed = Seq.empty[Int]
    var cycles = 0

    SimConfig
      .withWave
      .workspacePath("generated/simWorkspace")
      .compile(new DecodeMatVecInt8(cfg))
      .doSim { dut =>
        dut.clockDomain.forkStimulus(period = 10)
        dut.io.start #= false

        for (idx <- 0 until cfg.inputDim) {
          dut.io.activation(idx) #= activation(idx)
        }
        for (row <- 0 until cfg.outputDim) {
          for (col <- 0 until cfg.inputDim) {
            dut.io.weights(row)(col) #= weights(row)(col)
          }
        }

        dut.clockDomain.waitSampling()
        dut.io.start #= true
        dut.clockDomain.waitSampling()
        dut.io.start #= false

        cycles = 0
        val timeout = ((cfg.inputDim / cfg.tileDim) * cfg.outputDim) + 12
        while (!dut.io.done.toBoolean && cycles < timeout) {
          dut.clockDomain.waitSampling()
          cycles += 1
        }

        assert(dut.io.done.toBoolean, s"DecodeMatVecInt8 did not complete after $cycles cycles")

        observed = (0 until cfg.outputDim).map { idx =>
          dut.io.outputs(idx).toInt
        }

        assert(observed == expected, s"expected ${expected.mkString(",")} but observed ${observed.mkString(",")}")
      }

    (observed, cycles)
  }

  test("DecodeMatVecInt8 matches deterministic software reference") {
    val cfg = DecodeMatVecInt8.DemoConfig
    val expected = DecodeMatVecInt8Stimulus.expectedOutputs(cfg)
    val (observed, cycles) = runCoreSimulation(cfg)

    val repoRoot = new File("../..").getCanonicalFile
    val paper = new File(repoRoot, "assets/c10.csv")
    paper.getParentFile.mkdirs()

    def writeCsv(file: File): Unit = {
      val out = new PrintWriter(file)
      try {
        out.println("output_index,expected,observed,pass,input_dim,output_dim,tile_dim,cycles")
        for (idx <- 0 until cfg.outputDim) {
          out.println(s"$idx,${expected(idx)},${observed(idx)},${expected(idx) == observed(idx)},${cfg.inputDim},${cfg.outputDim},${cfg.tileDim},$cycles")
        }
      } finally {
        out.close()
      }
    }

    writeCsv(paper)
    println(s"DecodeMatVecInt8Sim PASS: expected=${expected.mkString("[", ",", "]")} observed=${observed.mkString("[", ",", "]")} cycles=$cycles")
    println(s"Wrote ${paper.getPath}")
  }

  test("DecodeMatVecInt8 tileDim=4 matches deterministic software reference") {
    val cfg = DecodeMatVecInt8Config(inputDim = 64, outputDim = 16, tileDim = 4)
    val expected = DecodeMatVecInt8Stimulus.expectedOutputs(cfg)
    val (observed, cycles) = runCoreSimulation(cfg)
    assert(observed == expected)
    assert(cycles <= (cfg.inputDim / cfg.tileDim) * cfg.outputDim + 4)
  }
}
