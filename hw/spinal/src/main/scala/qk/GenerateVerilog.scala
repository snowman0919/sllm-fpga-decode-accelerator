package qk

import spinal.core._

import java.io.File

object GenerateVerilog {
  private def targetDir: File = {
    val dir = new File("generated")
    dir.mkdirs()
    dir
  }

  def main(args: Array[String]): Unit = {
    val outputDir = targetDir.getCanonicalPath
    val config = SpinalConfig(targetDirectory = outputDir, oneFilePerComponent = true)

    config.generateVerilog(new DotProductInt8Dim16)
    config.generateVerilog(new HexDisplay)
    config.generateVerilog(new De10LiteTop)

    println(s"Generated Verilog into: $outputDir")
    println(s"- $outputDir/DotProductInt8_dim16.v")
    println(s"- $outputDir/HexDisplay.v")
    println(s"- $outputDir/De10LiteTop.v")
  }
}
