package qk

import spinal.core._

class JtagDecodeMatVecRegTop extends Component {
  noIoPrefix()

  val io = new Bundle {
    val CLOCK_50 = in Bool ()
    val avs_address = in UInt (12 bits)
    val avs_read = in Bool ()
    val avs_write = in Bool ()
    val avs_writedata = in Bits (32 bits)
    val avs_readdata = out Bits (32 bits)
    val avs_waitrequest = out Bool ()
    val avs_readdatavalid = out Bool ()
    val LEDR = out Bits (10 bits)
    val HEX0 = out Bits (7 bits)
    val HEX1 = out Bits (7 bits)
    val HEX2 = out Bits (7 bits)
    val HEX3 = out Bits (7 bits)
    val HEX4 = out Bits (7 bits)
    val HEX5 = out Bits (7 bits)
  }

  val coreClockDomain = ClockDomain(
    clock = io.CLOCK_50,
    config = ClockDomainConfig(resetKind = BOOT)
  )

  val area = new ClockingArea(coreClockDomain) {
    val regBank = new DecodeMatVecRegBank
    regBank.io.address := io.avs_address
    regBank.io.read := io.avs_read
    regBank.io.write := io.avs_write
    regBank.io.writedata := io.avs_writedata
    io.avs_readdata := regBank.io.readdata
    io.avs_waitrequest := regBank.io.waitrequest
    io.avs_readdatavalid := regBank.io.readdatavalid

    val hex0 = new HexDisplay
    val hex1 = new HexDisplay
    val hex2 = new HexDisplay
    val hex3 = new HexDisplay
    val hex4 = new HexDisplay
    val hex5 = new HexDisplay

    hex0.io.nibble := regBank.io.debugStatus(3 downto 0)
    hex1.io.nibble := regBank.io.debugStatus(7 downto 4)
    hex2.io.nibble := regBank.io.debugSeq(3 downto 0)
    hex3.io.nibble := regBank.io.debugSeq(7 downto 4)
    hex4.io.nibble := io.avs_address(5 downto 2).asBits
    hex5.io.nibble := B(0, 4 bits)
    hex5.io.nibble(0) := io.avs_read
    hex5.io.nibble(1) := io.avs_write
    hex5.io.nibble(2) := io.avs_waitrequest
    hex5.io.nibble(3) := io.avs_readdatavalid

    io.HEX0 := hex0.io.segments
    io.HEX1 := hex1.io.segments
    io.HEX2 := hex2.io.segments
    io.HEX3 := hex3.io.segments
    io.HEX4 := hex4.io.segments
    io.HEX5 := hex5.io.segments

    io.LEDR := B(0, 10 bits)
    io.LEDR(7 downto 0) := regBank.io.debugStatus
    io.LEDR(8) := io.avs_read
    io.LEDR(9) := io.avs_write
  }
}
