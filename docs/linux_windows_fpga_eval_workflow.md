# Linux/Nix and Windows FPGA Evaluation Workflow

This repository uses a split workflow because Windows Pocket4 does not provide
the Nix development environment. Keep generation, paper artifact construction,
and reproducibility checks on Linux/Nix. Use Windows only for Quartus hardware
operations and real DE10-Lite board runs.

## Linux/Nix Role

Use the Linux/Nix machine for:

- SpinalHDL Verilog generation and mirror refresh.
- SpinalHDL register-bank simulation.
- Python script validation.
- ONNX Runtime CPU and MatMulInteger micrograph baseline generation.
- Quartus report extraction script validation.
- Paper tables, figures, manuscript updates, and dist package generation.
- Git commits and push/pull coordination.

Recommended Linux flow:

```bash
nix develop -c just fpga-jtag-verilog
nix develop -c just fpga-jtag-regbank-sim
python scripts/build_ort_fpga_comparison.py
python scripts/build_dist_package.py
python scripts/verify_dist_package.py
git add .
git commit -m "..."
git push
```

The convenience target below runs the Linux-side preparation and package checks
from inside a Nix shell:

```bash
nix develop -c just fpga-linux-prepare
```

## Windows Pocket4 Role

Use Windows Pocket4 only for:

- `git pull` or receiving an archive of the Linux-produced repository state.
- Quartus clean compile.
- `.sof` programming through USB-Blaster.
- System Console JTAG-to-Avalon register benchmark.
- Board log generation and return to Linux, or a focused commit/push containing
  only the board logs and paper-facing measured artifacts.

Do not put `nix develop` commands in Windows run steps. Windows should use
Quartus CLI tools and `py -3`.

Recommended Windows flow:

```powershell
git pull
cd quartus\de10_lite_jtag_matvec
quartus_sh.exe --flow compile de10_lite_jtag_matvec
cd ..\..
quartus_pgm.exe -m jtag -c "USB-Blaster [USB-0]" -o "p;quartus\de10_lite_jtag_matvec\output_files\de10_lite_jtag_matvec.sof"
py -3 windows\run_fpga_jtag_matvec.py --runs 20 --cable "USB-Blaster [USB-0]" --quartus-bin "C:\altera_lite\25.1std\quartus\sopc_builder\bin\system-console.exe" --keep-tcl --log-dir logs\jtag_cycle_counter_real_final
git add logs paper_assets docs paper dist
git commit -m "Archive Windows board run"
git push
```

If committing on Windows is inconvenient, compress `logs`, `paper_assets`, and
the relevant reports, copy them back to Linux, and perform the paper/dist update
there.

## Evidence Boundary

The Windows JTAG path is a correctness, invocation, and cycle-counter
measurement path for a fixed 16x4 INT8 Decode MatVec primitive. JTAG total
latency is System Console/JTAG invocation overhead. FPGA primitive compute
latency is taken only from the board-measured internal `COMPUTE_CYCLES`
register.

Do not report the JTAG path as full Gemma execution, full ONNX model
acceleration, custom ONNX Runtime operator speedup, or end-to-end sLLM inference
speedup.
