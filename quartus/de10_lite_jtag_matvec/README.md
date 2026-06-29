# DE10-Lite JTAG Register Decode MatVec

This scaffold prepares a USB-Blaster JTAG-to-Avalon Master path for invoking the fixed INT8 Decode MatVec primitive through a memory-mapped register bank.

Flow:

```text
Windows host
-> Quartus System Console Tcl
-> USB-Blaster JTAG
-> JTAG-to-Avalon Master IP
-> DecodeMatVec register bank
-> DecodeMatVecInt8_i16_o4
```

Scope:

- top/register module: `JtagDecodeMatVecRegTop`
- register bank: `DecodeMatVecRegBank`
- fixed accepted shape: `input_dim=16`, `output_dim=4`
- activation/weight write format: signed int8 in low 8 bits of 32-bit register words
- result read format: signed int32 two's complement

This is a host-to-FPGA invocation and correctness path. It is not a performance-optimized interface and is not evidence of full Gemma execution or end-to-end ONNX Runtime speedup.

## Verilog

Generate and mirror Verilog:

```bash
nix develop -c just fpga-jtag-verilog
```

Expected generated mirror files:

- `generated_verilog/DecodeMatVecInt8_i16_o4.v`
- `generated_verilog/DecodeMatVecRegBank.v`
- `generated_verilog/HexDisplay.v`
- `generated_verilog/JtagDecodeMatVecRegTop.v`

## Platform Designer

The intended integration is a Platform Designer system containing:

- Clock source: `CLOCK_50`
- Reset source: board reset or Platform Designer reset bridge
- JTAG-to-Avalon Master IP
- exported Avalon-MM slave connected to `JtagDecodeMatVecRegTop` register signals or a wrapper around `DecodeMatVecRegBank`

If Platform Designer generation is not automated on the host, follow `platform_designer/create_jtag_matvec_system.tcl` as a checklist and create the `.qsys` manually. Do not treat this scaffold as a successful compile until Quartus actually generates, compiles, and programs a design with the JTAG-to-Avalon Master connected.

## Host Runner

The Windows runner generates a System Console Tcl script and invokes `system-console` or `quartus_stp`:

```powershell
python windows\run_fpga_jtag_matvec.py --runs 10 --cable "USB-Blaster [USB-0]"
```

Without Quartus tools, USB-Blaster, or a JTAG-to-Avalon master service, the runner writes a skipped summary and exits gracefully without creating a paper benchmark row.
