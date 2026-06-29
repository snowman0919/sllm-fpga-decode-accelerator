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

    DotProductInt8Sweep.SupportedDims.foreach { dim =>
      config.generateVerilog(DotProductInt8Sweep.newNamedCore(dim))
      config.generateVerilog(new DotProductInt8SweepTop(dim))
    }
    config.generateVerilog(new DecodeMatVecInt8Demo)
    config.generateVerilog(new HexDisplay)
    config.generateVerilog(new De10LiteTop)
    config.generateVerilog(new DecodeMatVecDemoTop)
    config.generateVerilog(new UartDecodeMatVecTop)

    println(s"Generated Verilog into: $outputDir")
    DotProductInt8Sweep.SupportedDims.foreach { dim =>
      println(s"- $outputDir/${DotProductInt8Sweep.definitionName(dim)}.v")
      println(s"- $outputDir/${DotProductInt8Sweep.wrapperDefinitionName(dim)}.v")
    }
    println(s"- $outputDir/${DecodeMatVecInt8.definitionName(DecodeMatVecInt8.DemoConfig)}.v")
    println(s"- $outputDir/HexDisplay.v")
    println(s"- $outputDir/De10LiteTop.v")
    println(s"- $outputDir/DecodeMatVecDemoTop.v")
    println(s"- $outputDir/UartDecodeMatVecTop.v")
  }
}
