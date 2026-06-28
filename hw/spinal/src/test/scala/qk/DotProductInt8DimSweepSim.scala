package qk

import org.scalatest.funsuite.AnyFunSuite
import spinal.core.sim._
import spinal.sim._

import java.nio.charset.StandardCharsets
import java.nio.file.{Files, Path, Paths}

class DotProductInt8DimSweepSim extends AnyFunSuite {
  private val repoRoot: Path = Paths.get("..", "..").toFile.getCanonicalFile.toPath
  private val capturedCsv: Path = repoRoot.resolve("fpga_test/captured/dot_product_dim_sweep_sim.csv")
  private val paperCsv: Path = repoRoot.resolve("paper_assets/tables/dot_product_dim_sweep_sim.csv")

  private def csvLine(columns: Seq[String]): String =
    columns.map { value =>
      "\"" + value.replace("\"", "\"\"") + "\""
    }.mkString(",")

  test("DotProductInt8 dim sweep matches software reference") {
    val rows = DotProductInt8Sweep.SupportedDims.map { dim =>
      val cfg = DotProductInt8Sweep.configForDim(dim)
      val (query, key) = DotProductInt8Stimulus.deterministicPair(dim)
      val expected = DotProductInt8Stimulus.expectedScore(dim)
      var observed = 0
      var cycles = 0

      SimConfig
        .workspacePath(s"generated/simWorkspace/dim$dim")
        .compile(DotProductInt8Sweep.newNamedCore(dim))
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

          cycles = 0
          while (!dut.io.done.toBoolean && cycles < (cfg.dim + 8)) {
            dut.clockDomain.waitSampling()
            cycles += 1
          }

          assert(dut.io.done.toBoolean, s"dot product dim=$dim did not complete after $cycles cycles")

          observed = dut.io.score.toInt
          assert(observed == expected, s"dim=$dim expected $expected but observed $observed")
        }

      val expectedHex = f"${expected & 0xFFFF}%04X"
      println(s"DotProductInt8DimSweepSim PASS: dim=$dim expected=$expected observed=$observed cycles=$cycles")
      Seq(
        dim.toString,
        expected.toString,
        observed.toString,
        cycles.toString,
        (dim + 1).toString,
        expectedHex,
        "pass"
      )
    }

    val lines = Seq(
      csvLine(
        Seq(
          "dim",
          "expected_score",
          "observed_score",
          "observed_cycles",
          "estimated_cycles_sequential_mac",
          "expected_hex_low16",
          "status"
        )
      )
    ) ++ rows.map(csvLine)

    Seq(capturedCsv, paperCsv).foreach { path =>
      Files.createDirectories(path.getParent)
      Files.write(path, lines.mkString("\n").concat("\n").getBytes(StandardCharsets.UTF_8))
      println(s"Wrote $path")
    }
  }
}
