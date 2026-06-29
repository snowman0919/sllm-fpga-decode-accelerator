# DE10-Lite UART Decode MatVec

This Quartus scaffold targets the UART-callable fixed INT8 Decode MatVec primitive:

- top entity: `UartDecodeMatVecTop`
- primitive: `DecodeMatVecInt8_i16_o4`
- fixed accepted request shape: `input_dim=16`, `output_dim=4`
- transport: UART request/response protocol documented in `docs/uart_protocol.md`

This is a primitive invocation validation path only. It does not run Gemma 3 1B, does not patch the full ONNX graph, and does not claim end-to-end ONNX Runtime speedup.

Use:

```bash
nix develop -c just fpga-uart-verilog
nix develop -c just fpga-uart-quartus
```

The verified DE10-Lite pin QSF must include the board clock, switches, LEDs, HEX displays, and the chosen UART RX/TX pins. If UART pins are not present in the verified QSF, add them on the Windows/Quartus host before treating the bitstream as board-ready.

Board wiring is documented in `docs/de10_lite_uart_wiring.md`. A commented QSF starting point is available at `qsf/uart_pins.template.qsf`; it is not sourced automatically and contains no fake pin assignments.
