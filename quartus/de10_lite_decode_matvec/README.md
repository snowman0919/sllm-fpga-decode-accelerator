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

## Windows Programming

On the Windows host with the DE10-Lite attached, program the generated `.sof` with:

```powershell
quartus_pgm.exe -m jtag -c "USB-Blaster" -o "p;.\de10_lite_decode_matvec.sof"
```

If the cable name differs, list available cables first:

```powershell
quartus_pgm.exe -l
```

## Programming Status

A captured Windows Quartus Prime Programmer run successfully configured the board using `de10_lite_decode_matvec.sof` on `USB-Blaster [USB-0]` for device `10M50DAF484`. The programmer reported `configuration succeeded` and completed with `0 errors, 0 warnings`.

This status confirms bitstream configuration of the small INT8 Decode MatVec primitive demo only. It is not evidence that the DE10-Lite runs Gemma 3 1B, a complete sLLM, full KV-cache management, or an end-to-end ONNX Runtime acceleration flow.
