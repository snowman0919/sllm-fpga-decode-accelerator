# Decode MatVec Board Programming Validation

## Evidence Source

- Evidence type: Windows Quartus Prime Programmer screenshot
- Screenshot path: `/home/monad/.codex/attachments/e9168f11-e547-4c3c-99e2-ef7ec8497019/Screenshot 2026-06-29 at 10.11.08.png`
- Programming host: Windows machine with DE10-Lite attached
- Programming command form: `quartus_pgm.exe -m jtag -c "USB-Blaster" -o "p;.\de10_lite_decode_matvec.sof"`

## Observed Programmer Log

- Quartus Prime Programmer version: `25.1std.0 Build 1129 10/21/2025 SC Lite Edition`
- Cable: `USB-Blaster [USB-0]`
- Programming file: `de10_lite_decode_matvec.sof`
- Target device: `10M50DAF484`
- Operation: JTAG programming/configuration
- Status: configuration succeeded
- Final result: `0 errors, 0 warnings`

## Interpretation

This validates that the DE10-Lite FPGA was successfully configured with the Decode MatVec demo bitstream. The evidence is limited to bitstream programming success for the small fixed-dimension INT8 Decode MatVec primitive demo.

This does not show that the FPGA runs Gemma 3 1B, a complete small language model, full KV-cache storage or movement, or an end-to-end ONNX Runtime acceleration path. Numeric board-output validation of the MatVec accumulator values should be recorded separately from `HEX3..HEX0` or `LEDR` observations.
