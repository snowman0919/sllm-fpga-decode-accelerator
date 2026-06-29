package qk

import java.io.File
import java.io.PrintWriter

import org.scalatest.funsuite.AnyFunSuite
import spinal.core.sim._
import spinal.sim._

class DecodeMatVecInt8Sim extends AnyFunSuite {
  test("DecodeMatVecInt8 matches deterministic software reference") {
    val cfg = DecodeMatVecInt8.DemoConfig
    val activation = DecodeMatVecInt8Stimulus.deterministicActivation(cfg.inputDim)
    val weights = DecodeMatVecInt8Stimulus.deterministicWeights(cfg)
    val expected = DecodeMatVecInt8Stimulus.expectedOutputs(cfg)

    SimConfig
      .withWave
      .workspacePath("generated/simWorkspace")
      .compile(new DecodeMatVecInt8Demo)
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

        var cycles = 0
        val timeout = (cfg.inputDim * cfg.outputDim) + 12
        while (!dut.io.done.toBoolean && cycles < timeout) {
          dut.clockDomain.waitSampling()
          cycles += 1
        }

        assert(dut.io.done.toBoolean, s"DecodeMatVecInt8 did not complete after $cycles cycles")

        val observed = (0 until cfg.outputDim).map { idx =>
          dut.io.outputs(idx).toInt
        }

        assert(observed == expected, s"expected ${expected.mkString(",")} but observed ${observed.mkString(",")}")

        val repoRoot = new File("../..").getCanonicalFile
        val captured = new File(repoRoot, "fpga_test/captured/decode_matvec_int8_sim.csv")
        val paper = new File(repoRoot, "paper_assets/tables/decode_matvec_int8_sim.csv")
        Seq(captured.getParentFile, paper.getParentFile).foreach(_.mkdirs())

        def writeCsv(file: File): Unit = {
          val out = new PrintWriter(file)
          try {
            out.println("output_index,expected,observed,pass,input_dim,output_dim,cycles")
            for (idx <- 0 until cfg.outputDim) {
              out.println(s"$idx,${expected(idx)},${observed(idx)},${expected(idx) == observed(idx)},${cfg.inputDim},${cfg.outputDim},$cycles")
            }
          } finally {
            out.close()
          }
        }

        writeCsv(captured)
        writeCsv(paper)
        println(s"DecodeMatVecInt8Sim PASS: expected=${expected.mkString("[", ",", "]")} observed=${observed.mkString("[", ",", "]")} cycles=$cycles")
        println(s"Wrote ${captured.getPath}")
        println(s"Wrote ${paper.getPath}")
      }
  }
}
