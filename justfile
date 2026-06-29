set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

default:
  @just --list

env-info:
  #!/usr/bin/env bash
  echo "project_root: $(pwd)"
  echo "in_nix_shell: ${IN_NIX_SHELL:-0}"
  echo "java: $(command -v java || echo missing)"
  echo "sbt: $(command -v sbt || echo missing)"
  echo "python3: $(command -v python3 || echo missing)"
  echo "verilator: $(command -v verilator || echo missing)"
  echo "quartus_sh: $(command -v quartus_sh || echo missing)"
  if command -v java >/dev/null 2>&1; then
    java -version
  fi
  if command -v python3 >/dev/null 2>&1; then
    python3 --version
  fi

fpga-jtag-verilog: spinal-generate

spinal-generate:
  #!/usr/bin/env bash
  command -v sbt >/dev/null 2>&1 || { echo "sbt is required. Enter the Nix shell with 'nix develop' first."; exit 1; }
  cd hw/spinal
  sbt "runMain qk.GenerateVerilog"
  rm -f generated/DotProductInt8.v generated/DotProductInt8.lst

  jtag_mirror_dir="../../quartus/de10_lite_jtag_matvec/generated_verilog"
  sweep_mirror_dir="../../quartus/dim_sweep/generated_verilog"
  mkdir -p "$jtag_mirror_dir" "$sweep_mirror_dir"

  for file in DecodeMatVecInt8_i16_o4.v DecodeMatVecRegBank.v HexDisplay.v JtagDecodeMatVecRegTop.v; do
    if [ ! -f "generated/$file" ]; then
      echo "Missing generated Verilog: hw/spinal/generated/$file"
      exit 1
    fi
    cp "generated/$file" "$jtag_mirror_dir/$file"
  done

  for file in \
    DotProductInt8_dim16.v DotProductInt8_dim32.v DotProductInt8_dim64.v DotProductInt8_dim128.v \
    DotProductInt8SweepTop_dim16.v DotProductInt8SweepTop_dim32.v DotProductInt8SweepTop_dim64.v DotProductInt8SweepTop_dim128.v
  do
    if [ ! -f "generated/$file" ]; then
      echo "Missing generated Verilog: hw/spinal/generated/$file"
      exit 1
    fi
    cp "generated/$file" "$sweep_mirror_dir/$file"
  done

  echo "Mirrored JTAG Decode MatVec Verilog into quartus/de10_lite_jtag_matvec/generated_verilog/"
  echo "Mirrored dim-sweep Verilog into quartus/dim_sweep/generated_verilog/"

fpga-jtag-regbank-sim:
  #!/usr/bin/env bash
  command -v sbt >/dev/null 2>&1 || { echo "sbt is required. Enter the Nix shell with 'nix develop' first."; exit 1; }
  cd hw/spinal
  sbt "testOnly qk.DecodeMatVecRegBankSim"

fpga-linux-prepare:
  #!/usr/bin/env bash
  just fpga-jtag-verilog
  just fpga-jtag-regbank-sim
  python3 scripts/build_ort_fpga_comparison.py
  python3 scripts/build_dist_package.py
  python3 scripts/verify_dist_package.py

fpga-paper-package:
  #!/usr/bin/env bash
  command -v python3 >/dev/null 2>&1 || { echo "python3 is required. Enter the Nix shell with 'nix develop' first."; exit 1; }
  python3 scripts/build_ort_fpga_comparison.py
  python3 scripts/build_dist_package.py
  python3 scripts/verify_dist_package.py

fpga-jtag-quartus:
  #!/usr/bin/env bash
  command -v quartus_sh >/dev/null 2>&1 || { echo "quartus_sh is required on PATH. Run this on Windows Pocket4 or a Quartus host."; exit 1; }
  missing=0
  for file in DecodeMatVecInt8_i16_o4.v DecodeMatVecRegBank.v HexDisplay.v JtagDecodeMatVecRegTop.v; do
    if [ ! -f "quartus/de10_lite_jtag_matvec/generated_verilog/$file" ]; then
      missing=1
    fi
  done
  if [ "$missing" -ne 0 ]; then
    echo "JTAG Decode MatVec Verilog mirror is missing or incomplete. Running 'just spinal-generate' first."
    just spinal-generate
  fi
  cd quartus/de10_lite_jtag_matvec
  quartus_sh --flow compile de10_lite_jtag_matvec

fpga-jtag-program sof="quartus/de10_lite_jtag_matvec/output_files/de10_lite_jtag_matvec.sof" cable="USB-Blaster":
  #!/usr/bin/env bash
  command -v quartus_pgm >/dev/null 2>&1 || { echo "quartus_pgm is required on PATH. Run this on Windows Pocket4 or a Quartus host."; exit 1; }
  quartus_pgm -m jtag -c "{{cable}}" -o "p;{{sof}}"

fpga-jtag-benchmark runs="20" log_dir="logs/jtag_cycle_counter_clean_rebuild_final" quartus_bin="" cable="USB-Blaster [USB-0]":
  #!/usr/bin/env bash
  command -v python3 >/dev/null 2>&1 || { echo "python3 is required."; exit 1; }
  args=(--runs "{{runs}}" --cable "{{cable}}" --log-dir "{{log_dir}}")
  if [ -n "{{quartus_bin}}" ]; then
    args+=(--quartus-bin "{{quartus_bin}}")
  fi
  python3 windows/run_fpga_jtag_matvec.py "${args[@]}"

verify:
  #!/usr/bin/env bash
  python3 -m py_compile \
    scripts/extract_quartus_summary.py \
    scripts/build_ort_fpga_comparison.py \
    scripts/build_dist_package.py \
    scripts/verify_dist_package.py \
    windows/run_fpga_jtag_matvec.py \
    windows/run_cpu_matvec_baseline.py \
    windows/run_ort_matvec_baseline.py \
    windows/run_ort_matvec_integer_baseline.py
  python3 scripts/build_ort_fpga_comparison.py
  python3 scripts/build_dist_package.py
  python3 scripts/verify_dist_package.py
  git diff --check

clean-generated:
  #!/usr/bin/env bash
  rm -f hw/spinal/generated/*.v
  rm -f hw/spinal/generated/*.lst
  rm -rf hw/spinal/generated/simWorkspace
  rm -f quartus/de10_lite_jtag_matvec/generated_verilog/*.v
  rm -f quartus/dim_sweep/generated_verilog/*.v
  rm -rf quartus/dim_sweep/projects
  rm -rf quartus/de10_lite_jtag_matvec/db
  rm -rf quartus/de10_lite_jtag_matvec/incremental_db
  rm -rf quartus/de10_lite_jtag_matvec/output_files
  echo "Generated Verilog and Quartus output directories removed."
