set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

quartus_helper := "quartus/de10_lite_qk/scripts/quartus_env.sh"

default:
  @just --list

env-info:
  #!/usr/bin/env bash
  echo "project_root: $(pwd)"
  echo "in_nix_shell: ${IN_NIX_SHELL:-0}"
  echo "java: $(command -v java || echo missing)"
  echo "sbt: $(command -v sbt || echo missing)"
  echo "scala: $(command -v scala || echo missing)"
  echo "python3: $(command -v python3 || echo missing)"
  echo "verilator: $(command -v verilator || echo missing)"
  echo "quartus_sh: $(command -v quartus_sh || echo missing)"
  if command -v java >/dev/null 2>&1; then
    java -version
  fi
  if command -v python3 >/dev/null 2>&1; then
    python3 --version
  fi

spinal-generate:
  #!/usr/bin/env bash
  command -v sbt >/dev/null 2>&1 || { echo "sbt is required. Enter the Nix shell with 'nix develop' first."; exit 1; }
  cd hw/spinal
  sbt "runMain qk.GenerateVerilog"
  rm -f generated/DotProductInt8.v generated/DotProductInt8.lst
  mirror_dir="../../quartus/de10_lite_qk/generated_verilog"
  mkdir -p "$mirror_dir"
  for file in DotProductInt8_dim16.v HexDisplay.v De10LiteTop.v; do
    if [ ! -f "generated/$file" ]; then
      echo "Missing generated Verilog: hw/spinal/generated/$file"
      exit 1
    fi
    cp "generated/$file" "$mirror_dir/$file"
  done
  echo "Mirrored canonical Verilog into quartus/de10_lite_qk/generated_verilog/"

spinal-sim:
  #!/usr/bin/env bash
  command -v sbt >/dev/null 2>&1 || { echo "sbt is required. Enter the Nix shell with 'nix develop' first."; exit 1; }
  cd hw/spinal
  sbt "testOnly qk.DotProductInt8Sim"

vectors dim="16" num_keys="8" seed="7" out_dir="fpga_test/vectors":
  #!/usr/bin/env bash
  command -v python3 >/dev/null 2>&1 || { echo "python3 is required. Enter the Nix shell with 'nix develop' first."; exit 1; }
  python3 onnx_profile/export_vectors.py --dim "{{dim}}" --num-keys "{{num_keys}}" --seed "{{seed}}" --out-dir "{{out_dir}}"

kv-cache-table layers="18" kv_heads="1" head_dim="256" bytes_per_element="2" out_dir="onnx_profile/results":
  #!/usr/bin/env bash
  command -v python3 >/dev/null 2>&1 || { echo "python3 is required. Enter the Nix shell with 'nix develop' first."; exit 1; }
  python3 onnx_profile/kv_cache_size.py     --layers "{{layers}}"     --kv-heads "{{kv_heads}}"     --head-dim "{{head_dim}}"     --bytes-per-element "{{bytes_per_element}}"     --out-dir "{{out_dir}}"

onnx-profile model="" provider="CPUExecutionProvider" prompt_len="128" decode_tokens="16" profile="0" out_dir="onnx_profile/results/raw":
  #!/usr/bin/env bash
  command -v python3 >/dev/null 2>&1 || { echo "python3 is required. Enter the Nix shell with 'nix develop' first."; exit 1; }
  args=(--provider "{{provider}}" --prompt-len "{{prompt_len}}" --decode-tokens "{{decode_tokens}}" --out-dir "{{out_dir}}")
  if [ "{{profile}}" = "1" ]; then
    args+=(--profile)
  fi
  if [ -n "{{model}}" ]; then
    args+=(--model "{{model}}")
  fi
  python3 onnx_profile/run_profile.py "${args[@]}"

onnx-decode-sweep model="" provider="CPUExecutionProvider" prompt_lens="128 512 1024 2048 4096" decode_tokens="8" profile="0" layers="18" kv_heads="1" head_dim="256" bytes_per_element="2" out_dir="onnx_profile/results":
  #!/usr/bin/env bash
  command -v python3 >/dev/null 2>&1 || { echo "python3 is required. Enter the Nix shell with 'nix develop' first."; exit 1; }
  [ -n "{{model}}" ] || { echo "An ONNX model path is required. Example: just onnx-decode-sweep /absolute/path/to/gemma3-1b.onnx"; exit 1; }
  args=(
    --model "{{model}}"
    --provider "{{provider}}"
    --decode-tokens "{{decode_tokens}}"
    --layers "{{layers}}"
    --kv-heads "{{kv_heads}}"
    --head-dim "{{head_dim}}"
    --bytes-per-element "{{bytes_per_element}}"
    --out-dir "{{out_dir}}"
    --paper-tables-dir "paper_assets/tables"
    --fpga-summary "fpga_test/captured/fpga_validation_summary.md"
    --prompt-lens {{prompt_lens}}
  )
  if [ "{{profile}}" = "1" ]; then
    args+=(--profile)
  fi
  python3 onnx_profile/decode_context_sweep.py "${args[@]}"

onnx-decode-summary:
  #!/usr/bin/env bash
  [ -f onnx_profile/results/decode_fpga_bridge_summary.md ] || { echo "Missing onnx_profile/results/decode_fpga_bridge_summary.md. Run 'just onnx-decode-sweep /absolute/path/to/model.onnx' first."; exit 1; }
  sed -n '1,240p' onnx_profile/results/decode_fpga_bridge_summary.md

quartus-check:
  #!/usr/bin/env bash
  source "{{quartus_helper}}"
  quartus_setup_path || true
  echo "QUARTUS_ROOT: ${QUARTUS_ROOT:-unset}"
  for tool in quartus_sh quartus_map quartus_fit quartus_asm quartus_pgm; do
    if path=$(quartus_find_tool "$tool"); then
      echo "which $tool: $path"
    else
      echo "which $tool: missing"
    fi
  done
  if path=$(quartus_find_tool quartus_sh); then
    echo "quartus_sh --version:"
    "$path" --version || echo "quartus_sh --version failed"
  else
    echo "quartus_sh --version: unavailable because quartus_sh was not found"
  fi
  echo "USB-Blaster check: run 'quartus_pgm -l' after connecting the board and ensuring udev/permissions are configured."

quartus-project:
  #!/usr/bin/env bash
  source "{{quartus_helper}}"
  missing=0
  for file in DotProductInt8_dim16.v HexDisplay.v De10LiteTop.v; do
    if [ ! -f "quartus/de10_lite_qk/generated_verilog/$file" ]; then
      missing=1
    fi
  done
  if [ "$missing" -ne 0 ]; then
    echo "Quartus Verilog mirror is missing or incomplete. Running 'just spinal-generate' first."
    just spinal-generate
  fi
  quartus_sh=$(quartus_find_tool quartus_sh) || {
    echo "quartus_sh not found. Set QUARTUS_ROOT or add Quartus to PATH."
    exit 1
  }
  if [ ! -f quartus/de10_lite_qk/qsf/verified_de10_lite_pins.qsf ]; then
    echo "warning: verified QSF is missing. Project will be created without board pin assignments."
  fi
  "$quartus_sh" -t quartus/de10_lite_qk/scripts/create_project.tcl
  qpf="quartus/de10_lite_qk/de10_lite_qk.qpf"
  qsf="quartus/de10_lite_qk/de10_lite_qk.qsf"
  [ -f "$qpf" ] || { echo "Quartus project file was not created: $qpf"; exit 1; }
  [ -f "$qsf" ] || { echo "Quartus settings file was not created: $qsf"; exit 1; }
  echo "Quartus project created: $qpf"
  echo "Quartus settings file created: $qsf"

quartus-compile:
  #!/usr/bin/env bash
  source "{{quartus_helper}}"
  quartus_sh=$(quartus_find_tool quartus_sh) || {
    echo "quartus_sh not found. Set QUARTUS_ROOT or add Quartus to PATH."
    exit 1
  }
  [ -f quartus/de10_lite_qk/de10_lite_qk.qpf ] || {
    echo "Quartus project has not been created yet. Run 'just quartus-project' first."
    exit 1
  }
  [ -f quartus/de10_lite_qk/qsf/verified_de10_lite_pins.qsf ] || {
    echo "Verified DE10-Lite QSF is missing. Import one with 'just import-qsf /path/to/verified.qsf' before compile."
    exit 1
  }
  "$quartus_sh" -t quartus/de10_lite_qk/scripts/compile.tcl

quartus-program:
  #!/usr/bin/env bash
  source "{{quartus_helper}}"
  quartus_sh=$(quartus_find_tool quartus_sh) || {
    echo "quartus_sh not found. Set QUARTUS_ROOT or add Quartus to PATH."
    exit 1
  }
  quartus_find_tool quartus_pgm >/dev/null || {
    echo "quartus_pgm not found. Set QUARTUS_ROOT or add Quartus programmer tools to PATH."
    exit 1
  }
  [ -f quartus/de10_lite_qk/output_files/de10_lite_qk.sof ] || {
    echo "Programming file missing. Run 'just quartus-compile' after importing a verified QSF."
    exit 1
  }
  "$quartus_sh" -t quartus/de10_lite_qk/scripts/program_sof.tcl

fpga-report quartus_dir="quartus/de10_lite_qk/output_files" out_dir="." expected_score="-22" expected_hex="FFEA":
  #!/usr/bin/env bash
  command -v python3 >/dev/null 2>&1 || { echo "python3 is required. Enter the Nix shell with 'nix develop' first."; exit 1; }
  python3 fpga_test/collect_quartus_reports.py \
    --quartus-dir "{{quartus_dir}}" \
    --out-dir "{{out_dir}}" \
    --expected-score "{{expected_score}}" \
    --expected-hex "{{expected_hex}}"

fpga-validate-summary:
  #!/usr/bin/env bash
  [ -f fpga_test/captured/fpga_validation_summary.md ] || just fpga-report
  sed -n '1,220p' fpga_test/captured/fpga_validation_summary.md

import-qsf qsf_path:
  #!/usr/bin/env bash
  quartus/de10_lite_qk/scripts/import_verified_qsf.sh "{{qsf_path}}"

de10-lite-checklist:
  #!/usr/bin/env bash
  source "{{quartus_helper}}"
  quartus_setup_path || true
  status() {
    local label="$1"
    local path="$2"
    if [ -e "$path" ]; then
      echo "[ok] $label: $path"
    else
      echo "[missing] $label: $path"
    fi
  }
  echo "DE10-Lite board validation checklist"
  status "canonical Spinal Verilog" "hw/spinal/generated/DotProductInt8_dim16.v"
  status "canonical Spinal Verilog" "hw/spinal/generated/HexDisplay.v"
  status "canonical Spinal Verilog" "hw/spinal/generated/De10LiteTop.v"
  status "Quartus mirror" "quartus/de10_lite_qk/generated_verilog/DotProductInt8_dim16.v"
  status "Quartus mirror" "quartus/de10_lite_qk/generated_verilog/HexDisplay.v"
  status "Quartus mirror" "quartus/de10_lite_qk/generated_verilog/De10LiteTop.v"
  status "placeholder QSF" "quartus/de10_lite_qk/qsf/de10_lite_pins.placeholder.qsf"
  status "verified QSF" "quartus/de10_lite_qk/qsf/verified_de10_lite_pins.qsf"
  status "Quartus project Tcl" "quartus/de10_lite_qk/scripts/create_project.tcl"
  status "Quartus compile Tcl" "quartus/de10_lite_qk/scripts/compile.tcl"
  status "Quartus program Tcl" "quartus/de10_lite_qk/scripts/program_sof.tcl"
  status "Quartus project file" "quartus/de10_lite_qk/de10_lite_qk.qpf"
  status "Quartus settings file" "quartus/de10_lite_qk/de10_lite_qk.qsf"
  status "SOF output" "quartus/de10_lite_qk/output_files/de10_lite_qk.sof"
  if path=$(quartus_find_tool quartus_sh); then
    echo "[ok] quartus_sh: $path"
  else
    echo "[missing] quartus_sh: set QUARTUS_ROOT or add Quartus to PATH"
  fi
  if path=$(quartus_find_tool quartus_pgm); then
    echo "[ok] quartus_pgm: $path"
  else
    echo "[missing] quartus_pgm: set QUARTUS_ROOT or add Quartus programmer tools to PATH"
  fi
  echo "Expected deterministic score low 16 bits after run: 0xFFEA"
  echo "HEX suggestion: HEX3..HEX0 should settle to F F E A after a successful board compile/program."

clean-generated:
  #!/usr/bin/env bash
  rm -rf hw/spinal/generated/*.v
  rm -rf hw/spinal/generated/*.lst
  rm -rf hw/spinal/generated/simWorkspace
  rm -rf quartus/de10_lite_qk/generated_verilog/*.v
  rm -rf quartus/de10_lite_qk/db
  rm -rf quartus/de10_lite_qk/incremental_db
  rm -rf quartus/de10_lite_qk/output_files
  rm -rf onnx_profile/results/raw/*
  rm -rf onnx_profile/results/tables/*
  rm -rf onnx_profile/results/figures/*
  rm -f onnx_profile/results/decode_fpga_bridge_summary.md
  find fpga_test/vectors -mindepth 1 -type f ! -name 'README.md' -delete
  find paper_assets/tables -mindepth 1 -type f ! -name 'README.md' ! -name '.gitkeep' -delete
  rm -f fpga_test/captured/fpga_validation_summary.md
  echo "Generated outputs removed from generated/results/assets directories."
