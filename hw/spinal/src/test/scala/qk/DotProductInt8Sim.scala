package qk

import org.scalatest.funsuite.AnyFunSuite
import spinal.core.sim._
import spinal.sim._

class DotProductInt8Sim extends AnyFunSuite {
  test("DotProductInt8 matches software reference") {
    val cfg = DotProductInt8Sweep.configForDim(16)
    val (query, key) = DotProductInt8Stimulus.deterministicPair(cfg.dim)
    val expected = DotProductInt8Stimulus.expectedScore(cfg.dim)

    SimConfig
      .withWave
      .workspacePath("generated/simWorkspace")
      .compile(new DotProductInt8Dim16)
      .doSim { dut =>
        dut.clockDomain.forkStimulus(period = 10)
        dut.io.start #= false

        for (idx <- 0 until cfg.dim) {
          dut.io.query(idx) #= query(idx)
          dut.io.key(idx) #= key(idx)
        }

        dut.clockDomain.waitSampling()
        dut.io.start #= true
        dut.clockDomain.waitSampling()
        dut.io.start #= false

        var cycles = 0
        while (!dut.io.done.toBoolean && cycles < (cfg.dim + 8)) {
          dut.clockDomain.waitSampling()
          cycles += 1
        }

        assert(dut.io.done.toBoolean, s"dot product did not complete after $cycles cycles")

        val observed = dut.io.score.toInt
        assert(observed == expected, s"expected $expected but observed $observed")
        println(s"DotProductInt8Sim PASS: expected=$expected observed=$observed cycles=$cycles")
      }
  }
}
