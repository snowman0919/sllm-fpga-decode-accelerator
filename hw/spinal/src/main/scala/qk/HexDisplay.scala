package qk

import spinal.core._

class HexDisplay extends Component {
  val io = new Bundle {
    val nibble = in Bits (4 bits)
    val segments = out Bits (7 bits)
  }

  io.segments := B"7'b1111111"

  switch(io.nibble) {
    is(B"4'h0") { io.segments := B"7'b1000000" }
    is(B"4'h1") { io.segments := B"7'b1111001" }
    is(B"4'h2") { io.segments := B"7'b0100100" }
    is(B"4'h3") { io.segments := B"7'b0110000" }
    is(B"4'h4") { io.segments := B"7'b0011001" }
    is(B"4'h5") { io.segments := B"7'b0010010" }
    is(B"4'h6") { io.segments := B"7'b0000010" }
    is(B"4'h7") { io.segments := B"7'b1111000" }
    is(B"4'h8") { io.segments := B"7'b0000000" }
    is(B"4'h9") { io.segments := B"7'b0010000" }
    is(B"4'hA") { io.segments := B"7'b0001000" }
    is(B"4'hB") { io.segments := B"7'b0000011" }
    is(B"4'hC") { io.segments := B"7'b1000110" }
    is(B"4'hD") { io.segments := B"7'b0100001" }
    is(B"4'hE") { io.segments := B"7'b0000110" }
    is(B"4'hF") { io.segments := B"7'b0001110" }
  }
}
