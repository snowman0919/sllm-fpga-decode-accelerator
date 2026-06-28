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
  sweep_mirror_dir="../../quartus/dim_sweep/generated_verilog"
  mkdir -p "$mirror_dir"
  mkdir -p "$sweep_mirror_dir"
  for file in DotProductInt8_dim16.v HexDisplay.v De10LiteTop.v; do
    if [ ! -f "generated/$file" ]; then
      echo "Missing generated Verilog: hw/spinal/generated/$file"
      exit 1
    fi
    cp "generated/$file" "$mirror_dir/$file"
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
  echo "Mirrored canonical Verilog into quartus/de10_lite_qk/generated_verilog/"
  echo "Mirrored dim-sweep Verilog into quartus/dim_sweep/generated_verilog/"

spinal-generate-sweep:
  #!/usr/bin/env bash
  just spinal-generate

spinal-sim:
  #!/usr/bin/env bash
  command -v sbt >/dev/null 2>&1 || { echo "sbt is required. Enter the Nix shell with 'nix develop' first."; exit 1; }
  cd hw/spinal
  sbt "testOnly qk.DotProductInt8Sim"

spinal-sim-sweep:
  #!/usr/bin/env bash
  command -v sbt >/dev/null 2>&1 || { echo "sbt is required. Enter the Nix shell with 'nix develop' first."; exit 1; }
  cd hw/spinal
  sbt "testOnly qk.DotProductInt8DimSweepSim"

vectors dim="16" num_keys="8" seed="7" out_dir="fpga_test/vectors":
  #!/usr/bin/env bash
  command -v python3 >/dev/null 2>&1 || { echo "python3 is required. Enter the Nix shell with 'nix develop' first."; exit 1; }
  python3 onnx_profile/export_vectors.py --dim "{{dim}}" --num-keys "{{num_keys}}" --seed "{{seed}}" --out-dir "{{out_dir}}"

torch-gemma-profile model_dir="/home/monad/develop/ai_accel/gemma3-1B" prompt="Explain KV cache in one sentence." new_tokens="8" device="cpu" dtype="bfloat16" out_dir="onnx_profile/results":
  #!/usr/bin/env bash
  command -v python3 >/dev/null 2>&1 || { echo "python3 is required. Enter the Nix shell with 'nix develop' first."; exit 1; }
  resolved_model_dir="{{model_dir}}"
  resolved_model_dir="${resolved_model_dir#model_dir=}"
  resolved_out_dir="{{out_dir}}"
  resolved_out_dir="${resolved_out_dir#out_dir=}"
  python3 onnx_profile/profile_torch_gemma.py \
    --model-dir "$resolved_model_dir" \
    --prompt "{{prompt}}" \
    --new-tokens "{{new_tokens}}" \
    --device "{{device}}" \
    --dtype "{{dtype}}" \
    --out-dir "$resolved_out_dir"

hf-inspect model_dir="/home/monad/develop/ai_accel/gemma3-1B" out_dir="onnx_profile/results":
  #!/usr/bin/env bash
  command -v python3 >/dev/null 2>&1 || { echo "python3 is required. Enter the Nix shell with 'nix develop' first."; exit 1; }
  resolved_model_dir="{{model_dir}}"
  resolved_model_dir="${resolved_model_dir#model_dir=}"
  resolved_out_dir="{{out_dir}}"
  resolved_out_dir="${resolved_out_dir#out_dir=}"
  python3 onnx_profile/inspect_hf_model_dir.py --model-dir "$resolved_model_dir" --out-dir "$resolved_out_dir"

gemma-onnx-export-dry model_dir="/home/monad/develop/ai_accel/gemma3-1B" out_dir="/home/monad/develop/ai_accel/gemma3-1B-onnx" task="text-generation-with-past" opset="17" device="cpu":
  #!/usr/bin/env bash
  command -v python3 >/dev/null 2>&1 || { echo "python3 is required. Enter the Nix shell with 'nix develop' first."; exit 1; }
  resolved_model_dir="{{model_dir}}"
  resolved_model_dir="${resolved_model_dir#model_dir=}"
  resolved_out_dir="{{out_dir}}"
  resolved_out_dir="${resolved_out_dir#out_dir=}"
  python3 onnx_profile/export_gemma_to_onnx.py \
    --model-dir "$resolved_model_dir" \
    --out-dir "$resolved_out_dir" \
    --task "{{task}}" \
    --opset "{{opset}}" \
    --device "{{device}}" \
    --dry-run

gemma-onnx-export model_dir="/home/monad/develop/ai_accel/gemma3-1B" out_dir="/home/monad/develop/ai_accel/gemma3-1B-onnx" task="text-generation-with-past" opset="17" device="cpu":
  #!/usr/bin/env bash
  command -v python3 >/dev/null 2>&1 || { echo "python3 is required. Enter the Nix shell with 'nix develop' first."; exit 1; }
  resolved_model_dir="{{model_dir}}"
  resolved_model_dir="${resolved_model_dir#model_dir=}"
  resolved_out_dir="{{out_dir}}"
  resolved_out_dir="${resolved_out_dir#out_dir=}"
  python3 onnx_profile/export_gemma_to_onnx.py \
    --model-dir "$resolved_model_dir" \
    --out-dir "$resolved_out_dir" \
    --task "{{task}}" \
    --opset "{{opset}}" \
    --device "{{device}}"

onnx-inspect model="/path/to/exported/model.onnx" out_dir="onnx_profile/results":
  #!/usr/bin/env bash
  command -v python3 >/dev/null 2>&1 || { echo "python3 is required. Enter the Nix shell with 'nix develop' first."; exit 1; }
  resolved_model="{{model}}"
  resolved_model="${resolved_model#model=}"
  resolved_out_dir="{{out_dir}}"
  resolved_out_dir="${resolved_out_dir#out_dir=}"
  [ "$resolved_model" != "/path/to/exported/model.onnx" ] || { echo "Set a real ONNX model path. Example: nix develop -c just onnx-inspect model=/home/monad/develop/ai_accel/gemma3-1B-onnx/model.onnx"; exit 1; }
  python3 onnx_profile/inspect_onnx_model.py --model "$resolved_model" --out-dir "$resolved_out_dir"

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

onnx-export model_dir="/home/monad/develop/ai_accel/gemma3-1B" onnx_dir="/home/monad/develop/ai_accel/gemma3-1B-onnx" results_dir="onnx_profile/results_onnx" opset="17" device="cpu":
  #!/usr/bin/env bash
  command -v python3 >/dev/null 2>&1 || { echo "python3 is required. Enter the Nix shell with 'nix develop' first."; exit 1; }
  python3 onnx_profile/onnx_bottleneck_flow.py export \
    --model-dir "{{model_dir}}" \
    --onnx-dir "{{onnx_dir}}" \
    --results-dir "{{results_dir}}" \
    --paper-tables-dir "paper_assets/tables" \
    --report-path "docs/onnx_bottleneck_report.md" \
    --opset "{{opset}}" \
    --device "{{device}}"

ort-profile model="/home/monad/develop/ai_accel/gemma3-1B-onnx/model.onnx" results_dir="onnx_profile/results_onnx" prompt_len="32" decode_tokens="2":
  #!/usr/bin/env bash
  command -v python3 >/dev/null 2>&1 || { echo "python3 is required. Enter the Nix shell with 'nix develop' first."; exit 1; }
  python3 onnx_profile/onnx_bottleneck_flow.py profile \
    --model "{{model}}" \
    --results-dir "{{results_dir}}" \
    --paper-tables-dir "paper_assets/tables" \
    --report-path "docs/onnx_bottleneck_report.md" \
    --prompt-len "{{prompt_len}}" \
    --decode-tokens "{{decode_tokens}}"

onnx-bottleneck-report model="/home/monad/develop/ai_accel/gemma3-1B-onnx/model.onnx" results_dir="onnx_profile/results_onnx":
  #!/usr/bin/env bash
  command -v python3 >/dev/null 2>&1 || { echo "python3 is required. Enter the Nix shell with 'nix develop' first."; exit 1; }
  python3 onnx_profile/onnx_bottleneck_flow.py report \
    --model "{{model}}" \
    --results-dir "{{results_dir}}" \
    --paper-tables-dir "paper_assets/tables" \
    --report-path "docs/onnx_bottleneck_report.md"

ort-sweep model="/home/monad/develop/ai_accel/gemma3-1B-onnx/model.onnx" out_dir="onnx_profile/results_onnx_sweep" context_lengths="128 512 1024 2048" decode_steps="1 2 4 8" runs="3" warmup_runs="1":
  #!/usr/bin/env bash
  command -v python3 >/dev/null 2>&1 || { echo "python3 is required. Enter the Nix shell with 'nix develop' first."; exit 1; }
  python3 onnx_profile/ort_context_sweep.py sweep \
    --model "{{model}}" \
    --provider "CPUExecutionProvider" \
    --out-dir "{{out_dir}}" \
    --paper-tables-dir "paper_assets/tables" \
    --paper-figures-dir "paper_assets/figures" \
    --report-path "docs/onnx_runtime_sweep_report.md" \
    --context-lengths {{context_lengths}} \
    --decode-steps {{decode_steps}} \
    --runs "{{runs}}" \
    --warmup-runs "{{warmup_runs}}"

ort-sweep-report model="/home/monad/develop/ai_accel/gemma3-1B-onnx/model.onnx" out_dir="onnx_profile/results_onnx_sweep":
  #!/usr/bin/env bash
  command -v python3 >/dev/null 2>&1 || { echo "python3 is required. Enter the Nix shell with 'nix develop' first."; exit 1; }
  python3 onnx_profile/ort_context_sweep.py report \
    --model "{{model}}" \
    --provider "CPUExecutionProvider" \
    --out-dir "{{out_dir}}" \
    --paper-tables-dir "paper_assets/tables" \
    --paper-figures-dir "paper_assets/figures" \
    --report-path "docs/onnx_runtime_sweep_report.md"

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

torch-context-sweep model_dir="/home/monad/develop/ai_accel/gemma3-1B" out_dir="onnx_profile/results" device="auto" dtype="auto" context_lengths="128 512 1024 2048 4096" decode_tokens="8" runs="5" warmup_runs="1" prompt_source="" max_context="4096":
  #!/usr/bin/env bash
  command -v python3 >/dev/null 2>&1 || { echo "python3 is required. Enter the Nix shell with 'nix develop' first."; exit 1; }
  resolved_model_dir="{{model_dir}}"
  resolved_model_dir="${resolved_model_dir#model_dir=}"
  resolved_out_dir="{{out_dir}}"
  resolved_out_dir="${resolved_out_dir#out_dir=}"
  args=(
    --model-dir "$resolved_model_dir"
    --out-dir "$resolved_out_dir"
    --device "{{device}}"
    --dtype "{{dtype}}"
    --context-lengths {{context_lengths}}
    --decode-tokens "{{decode_tokens}}"
    --runs "{{runs}}"
    --warmup-runs "{{warmup_runs}}"
    --max-context "{{max_context}}"
  )
  if [ -n "{{prompt_source}}" ]; then
    args+=(--prompt-source "{{prompt_source}}")
  fi
  python3 onnx_profile/torch_context_sweep.py "${args[@]}"

torch-context-summary:
  #!/usr/bin/env bash
  status_json="onnx_profile/results/raw/torch_context_sweep_status.json"
  latency_csv="onnx_profile/results/tables/torch_decode_latency_by_context.csv"
  memory_csv="onnx_profile/results/tables/torch_memory_by_context.csv"
  [ -f "$status_json" ] || { echo "Missing $status_json. Run 'just torch-context-sweep model_dir=/home/monad/develop/ai_accel/gemma3-1B' first."; exit 1; }
  sed -n '1,220p' "$status_json"
  if [ -f "$latency_csv" ]; then
    echo
    echo "Latency table preview:"
    sed -n '1,12p' "$latency_csv"
  fi
  if [ -f "$memory_csv" ]; then
    echo
    echo "Memory table preview:"
    sed -n '1,12p' "$memory_csv"
  fi

torch-sweep-analysis config_json="" latency_csv="paper_assets/tables/torch_decode_latency_by_context.csv" memory_csv="paper_assets/tables/torch_memory_by_context.csv" layers="26" kv_heads="1" head_dim="256" bytes_per_element="2":
  #!/usr/bin/env bash
  command -v python3 >/dev/null 2>&1 || { echo "python3 is required. Enter the Nix shell with 'nix develop' first."; exit 1; }
  args=(
    --latency-csv "{{latency_csv}}"
    --memory-csv "{{memory_csv}}"
    --tables-dir "paper_assets/tables"
    --figures-dir "paper_assets/figures"
    --summary-md "paper_assets/torch_sweep_analysis_summary.md"
    --layers "{{layers}}"
    --kv-heads "{{kv_heads}}"
    --head-dim "{{head_dim}}"
    --bytes-per-element "{{bytes_per_element}}"
  )
  if [ -n "{{config_json}}" ]; then
    args+=(--config-json "{{config_json}}")
  fi
  python3 onnx_profile/analyze_torch_sweep.py "${args[@]}"

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

quartus-dim-sweep:
  #!/usr/bin/env bash
  command -v python3 >/dev/null 2>&1 || { echo "python3 is required. Enter the Nix shell with 'nix develop' first."; exit 1; }
  source "{{quartus_helper}}"
  if [ ! -f "quartus/dim_sweep/generated_verilog/DotProductInt8_dim128.v" ]; then
    echo "Dim-sweep Verilog mirror is missing or incomplete. Running 'just spinal-generate-sweep' first."
    just spinal-generate-sweep
  fi
  quartus_sh=$(quartus_find_tool quartus_sh) || {
    echo "quartus_sh not found. Set QUARTUS_ROOT or add Quartus to PATH."
    exit 1
  }
  python3 fpga_test/run_quartus_dim_sweep.py \
    --quartus-sh "$quartus_sh" \
    --repo-root .

fpga-dim-sweep-report:
  #!/usr/bin/env bash
  command -v python3 >/dev/null 2>&1 || { echo "python3 is required. Enter the Nix shell with 'nix develop' first."; exit 1; }
  [ -f fpga_test/captured/dot_product_dim_sweep_sim.csv ] || just spinal-sim-sweep
  python3 fpga_test/collect_dim_sweep_reports.py \
    --quartus-root quartus/dim_sweep \
    --out-dir . \
    --sim-csv fpga_test/captured/dot_product_dim_sweep_sim.csv

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
  rm -rf quartus/dim_sweep/generated_verilog/*.v
  rm -rf quartus/dim_sweep/projects
  rm -rf quartus/de10_lite_qk/db
  rm -rf quartus/de10_lite_qk/incremental_db
  rm -rf quartus/de10_lite_qk/output_files
  rm -rf onnx_profile/results/raw/*
  rm -rf onnx_profile/results/tables/*
  rm -rf onnx_profile/results/figures/*
  rm -f onnx_profile/results/decode_fpga_bridge_summary.md
  find fpga_test/vectors -mindepth 1 -type f ! -name 'README.md' -delete
  find paper_assets/tables -mindepth 1 -type f ! -name 'README.md' ! -name '.gitkeep' -delete
  find paper_assets/figures -mindepth 1 -type f ! -name 'README.md' ! -name '.gitkeep' ! -name '*.placeholder.md' -delete
  rm -f fpga_test/captured/fpga_validation_summary.md
  rm -f fpga_test/captured/dot_product_dim_sweep_sim.csv
  echo "Generated outputs removed from generated/results/assets directories."
