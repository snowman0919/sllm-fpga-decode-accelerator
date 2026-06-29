# DE10-Lite Decode MatVec Demo

This Quartus project targets the small fixed-dimension INT8 Decode MatVec primitive demo:

- top entity: `DecodeMatVecDemoTop`
- primitive: `DecodeMatVecInt8_i16_o4`
- input dimension: `16`
- output dimension: `4`
- output display: `SW[2:1]` selects one accumulator; `HEX3..HEX0` show its low 16 bits

The project is a synthesis/programming artifact only. It does not claim Gemma 3 1B execution, full KV-cache management, or end-to-end ONNX Runtime speedup.

Use:

```bash
nix develop -c just decode-matvec-quartus
```

If compile succeeds, the `.sof` is expected under:

```text
quartus/de10_lite_decode_matvec/output_files/de10_lite_decode_matvec.sof
```

Board programming is intentionally left to the Windows machine that has the DE10-Lite connected.
