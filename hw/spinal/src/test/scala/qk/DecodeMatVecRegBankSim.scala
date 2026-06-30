package qk

import java.io.File
import java.io.PrintWriter

import org.scalatest.funsuite.AnyFunSuite
import spinal.core.sim._

class DecodeMatVecRegBankSim extends AnyFunSuite {
  private def signed32(value: BigInt): Int = {
    val masked = value & BigInt("ffffffff", 16)
    if (masked >= BigInt("80000000", 16)) (masked - BigInt("100000000", 16)).toInt
    else masked.toInt
  }

  test("DecodeMatVecRegBank exposes result and cycle-counter registers") {
    val cfg = DecodeMatVecInt8.DemoConfig
    val activation = DecodeMatVecInt8Stimulus.deterministicActivation(cfg.inputDim)
    val weights = DecodeMatVecInt8Stimulus.deterministicWeights(cfg)
    val expected = DecodeMatVecInt8Stimulus.expectedOutputs(cfg)
    val seq = 42

    SimConfig
      .withWave
      .workspacePath("generated/simWorkspace")
      .compile(new DecodeMatVecRegBank)
      .doSim { dut =>
        dut.clockDomain.forkStimulus(period = 10)
        dut.io.address #= 0
        dut.io.read #= false
        dut.io.write #= false
        dut.io.writedata #= 0
        dut.clockDomain.waitSampling(2)

        def writeReg(offset: Int, value: BigInt): Unit = {
          dut.io.address #= offset
          dut.io.writedata #= value
          dut.io.read #= false
          dut.io.write #= true
          dut.clockDomain.waitSampling()
          dut.io.write #= false
          dut.io.writedata #= 0
          dut.clockDomain.waitSampling()
        }

        def readReg(offset: Int): BigInt = {
          dut.io.address #= offset
          dut.io.read #= true
          dut.io.write #= false
          dut.clockDomain.waitSampling()
          val value = dut.io.readdata.toBigInt
          dut.io.read #= false
          dut.clockDomain.waitSampling()
          value
        }

        writeReg(DecodeMatVecRegMap.Control, 0x2)
        writeReg(DecodeMatVecRegMap.Seq, seq)
        for (idx <- 0 until cfg.inputDim) {
          writeReg(DecodeMatVecRegMap.ActivationBase + idx * 4, activation(idx) & 0xff)
        }
        for (row <- 0 until cfg.outputDim) {
          for (col <- 0 until cfg.inputDim) {
            val idx = row * cfg.inputDim + col
            writeReg(DecodeMatVecRegMap.WeightBase + idx * 4, weights(row)(col) & 0xff)
          }
        }

        writeReg(DecodeMatVecRegMap.Control, 0x1)

        var status = 0
        var pollCycles = 0
        while ((status & 0x2) == 0 && pollCycles < 128) {
          status = readReg(DecodeMatVecRegMap.Status).toInt
          pollCycles += 1
        }
        assert((status & 0x2) != 0, s"done bit was not set after $pollCycles status polls")

        val observed = (0 until cfg.outputDim).map { idx =>
          signed32(readReg(DecodeMatVecRegMap.ResultBase + idx * 4))
        }
        val computeCycles = readReg(DecodeMatVecRegMap.ComputeCycles).toInt
        val coreTotalCycles = readReg(DecodeMatVecRegMap.CoreTotalCycles).toInt
        val lastRunId = readReg(DecodeMatVecRegMap.LastRunId).toInt
        val debugStatus = readReg(DecodeMatVecRegMap.DebugStatus).toInt

        assert(observed == expected, s"expected ${expected.mkString(",")} but observed ${observed.mkString(",")}")
        assert(lastRunId == seq, s"expected LAST_RUN_ID=$seq but observed $lastRunId")
        assert(computeCycles >= 60 && computeCycles <= 80, s"unexpected COMPUTE_CYCLES=$computeCycles")
        assert(coreTotalCycles >= computeCycles, s"CORE_TOTAL_CYCLES=$coreTotalCycles should be >= COMPUTE_CYCLES=$computeCycles")
        assert((debugStatus & 0x2) != 0, s"DEBUG_STATUS done_latched bit not set: $debugStatus")

        val repoRoot = new File("../..").getCanonicalFile
        val paper = new File(repoRoot, "assets/sim_reg.csv")
        paper.getParentFile.mkdirs()

        def writeCsv(file: File): Unit = {
          val out = new PrintWriter(file)
          try {
            out.println("seq,expected,result,pass,compute_cycles,core_total_cycles,last_run_id,debug_status,input_dim,output_dim,cycle_boundary")
            out.println(
              Seq(
                seq,
                expected.mkString(" "),
                observed.mkString(" "),
                observed == expected,
                computeCycles,
                coreTotalCycles,
                lastRunId,
                debugStatus,
                cfg.inputDim,
                cfg.outputDim,
                "simulation_only_not_board_measurement"
              ).mkString(",")
            )
          } finally {
            out.close()
          }
        }

        writeCsv(paper)
        println(
          s"DecodeMatVecRegBankSim PASS: result=${observed.mkString("[", ",", "]")} compute_cycles=$computeCycles core_total_cycles=$coreTotalCycles"
        )
      }
  }
}
