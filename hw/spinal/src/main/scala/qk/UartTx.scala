package qk

import spinal.core._

class UartTx(clockHz: Int = 50000000, baudRate: Int = 115200) extends Component {
  val io = new Bundle {
    val valid = in Bool ()
    val data = in Bits (8 bits)
    val ready = out Bool ()
    val txd = out Bool ()
    val busy = out Bool ()
  }

  private val ticksPerBit = (clockHz + baudRate / 2) / baudRate
  private val counterWidth = Math.max(log2Up(ticksPerBit), 1)

  val counter = Reg(UInt(counterWidth bits)) init (0)
  val bitIndex = Reg(UInt(3 bits)) init (0)
  val shift = Reg(Bits(8 bits)) init (0)
  val txdReg = Reg(Bool()) init (True)
  val state = Reg(UInt(2 bits)) init (0)

  io.ready := state === 0
  io.busy := state =/= 0
  io.txd := txdReg

  switch(state) {
    is(0) {
      txdReg := True
      counter := 0
      bitIndex := 0
      when(io.valid) {
        shift := io.data
        txdReg := False
        state := 1
      }
    }
    is(1) {
      when(counter === U(ticksPerBit - 1, counterWidth bits)) {
        counter := 0
        txdReg := shift(0)
        state := 2
      } otherwise {
        counter := counter + 1
      }
    }
    is(2) {
      when(counter === U(ticksPerBit - 1, counterWidth bits)) {
        counter := 0
        when(bitIndex === U(7, 3 bits)) {
          txdReg := True
          state := 3
        } otherwise {
          bitIndex := bitIndex + 1
          txdReg := shift(bitIndex + 1)
        }
      } otherwise {
        counter := counter + 1
      }
    }
    is(3) {
      when(counter === U(ticksPerBit - 1, counterWidth bits)) {
        counter := 0
        state := 0
      } otherwise {
        counter := counter + 1
      }
    }
  }
}
