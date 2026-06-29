package qk

import spinal.core._

class UartRx(clockHz: Int = 50000000, baudRate: Int = 115200) extends Component {
  val io = new Bundle {
    val rxd = in Bool ()
    val valid = out Bool ()
    val data = out Bits (8 bits)
    val frameError = out Bool ()
  }

  private val ticksPerBit = (clockHz + baudRate / 2) / baudRate
  private val counterWidth = Math.max(log2Up(ticksPerBit), 1)

  val counter = Reg(UInt(counterWidth bits)) init (0)
  val bitIndex = Reg(UInt(3 bits)) init (0)
  val shift = Reg(Bits(8 bits)) init (0)
  val validReg = Reg(Bool()) init (False)
  val frameErrorReg = Reg(Bool()) init (False)
  val state = Reg(UInt(2 bits)) init (0)

  io.valid := validReg
  io.data := shift
  io.frameError := frameErrorReg

  validReg := False
  frameErrorReg := False

  switch(state) {
    is(0) {
      counter := 0
      bitIndex := 0
      when(!io.rxd) {
        state := 1
      }
    }
    is(1) {
      when(counter === U((ticksPerBit / 2).max(1) - 1, counterWidth bits)) {
        counter := 0
        when(!io.rxd) {
          state := 2
        } otherwise {
          state := 0
        }
      } otherwise {
        counter := counter + 1
      }
    }
    is(2) {
      when(counter === U(ticksPerBit - 1, counterWidth bits)) {
        counter := 0
        shift(bitIndex) := io.rxd
        when(bitIndex === U(7, 3 bits)) {
          state := 3
        } otherwise {
          bitIndex := bitIndex + 1
        }
      } otherwise {
        counter := counter + 1
      }
    }
    is(3) {
      when(counter === U(ticksPerBit - 1, counterWidth bits)) {
        counter := 0
        validReg := io.rxd
        frameErrorReg := !io.rxd
        state := 0
      } otherwise {
        counter := counter + 1
      }
    }
  }
}
