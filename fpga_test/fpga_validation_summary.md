# DE10-Lite FPGA Validation: INT8 QK Dot Product

The generated SpinalHDL RTL for the INT8 QK dot-product block was synthesized using Quartus Prime Lite 25.1std and programmed onto a DE10-Lite MAX 10 FPGA board.

The deterministic internal test vector produced a simulation result of `-22`. On the FPGA board, the lower 16-bit two's complement representation was displayed on the HEX display as:

```text
HEX3..HEX0 = F F E A

This corresponds to:
-22 = 0xFFFF_FFEA
lower 16 bits = 0xFFEA

This validation confirms that the synthesized FPGA design produces the expected result for the fixed INT8 dot-product test case. It does not imply that Gemma 3 1B or a full sLLM is running on the DE10-Lite board.
