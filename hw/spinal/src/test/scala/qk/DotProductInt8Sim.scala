package qk

import org.scalatest.funsuite.AnyFunSuite
import spinal.core.sim._
import spinal.sim._

class DotProductInt8Sim extends AnyFunSuite {
  test("DotProductInt8 matches software reference") {
    val cfg = DotProductInt8Config(dim = 16, dataWidth = 8, accWidth = 32)
    val query = Seq(-8, -7, -6, -5, -4, -3, -2, -1, 1, 2, 3, 4, 5, 6, 7, 8)
    val key = Seq(3, -1, 4, -2, 5, -3, 6, -4, 2, -5, 1, -6, 0, 7, -7, 8)
    val expected = query.zip(key).map { case (q, k) => q * k }.sum

    SimConfig
      .withWave
      .workspacePath("generated/simWorkspace")
      .compile(new DotProductInt8(cfg))
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
