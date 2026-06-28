#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
quartus_dir="$repo_root/quartus/de10_lite_qk"

source "$quartus_dir/scripts/quartus_env.sh"

usage() {
  cat <<'EOF'
Usage:
  ./scripts/quartus.sh check
  ./scripts/quartus.sh project
  ./scripts/quartus.sh compile
  ./scripts/quartus.sh program
  ./scripts/quartus.sh import-qsf <path-to-verified_de10_lite.qsf>

Notes:
  - Quartus is resolved from QUARTUS_ROOT, PATH, or common install roots such as
    $HOME/.intelFPGA_lite and $HOME/intelFPGA_lite.
  - These commands do not require nix develop.
  - SpinalHDL-generated Verilog must already exist before 'project'.
  - 'import-qsf' is only needed when you want to replace the current verified QSF.
  - Replace angle-bracket placeholders with a real path. Do not paste them literally.
EOF
}

require_tool() {
  local tool="$1"
  local path
  path="$(quartus_find_tool "$tool")" || {
    echo "$tool not found. Set QUARTUS_ROOT or add Quartus tools to PATH."
    exit 1
  }
  printf '%s\n' "$path"
}

check_jtag_lock() {
  local jtagconfig
  local output
  if ! jtagconfig="$(quartus_find_tool jtagconfig 2>/dev/null)"; then
    return 0
  fi
  output="$("$jtagconfig" 2>&1 || true)"
  if printf '%s\n' "$output" | grep -q "Insufficient port permissions"; then
    echo "$output"
    cat <<'EOF'

JTAG access is blocked by USB device permissions.
The USB-Blaster is visible, but the current user cannot lock the JTAG chain.

Typical fix on Linux:
  1. Create a udev rule for Altera USB-Blaster devices.
  2. Reload udev rules or replug the board.
  3. Restart jtagd, then retry.

Suggested rule contents:
  SUBSYSTEM=="usb", ATTR{idVendor}=="09fb", ATTR{idProduct}=="6001", MODE="0660", GROUP="plugdev"

Suggested commands as root:
  printf '%s\n' 'SUBSYSTEM=="usb", ATTR{idVendor}=="09fb", ATTR{idProduct}=="6001", MODE="0660", GROUP="plugdev"' > /etc/udev/rules.d/51-usbblaster.rules
  udevadm control --reload-rules
  udevadm trigger
  systemctl restart systemd-udevd
  pkill jtagd || true

Then unplug/replug the board and run:
  ./scripts/quartus.sh program
EOF
    return 1
  fi
  return 0
}

require_generated_verilog() {
  local missing=0
  local file
  for file in DotProductInt8_dim16.v HexDisplay.v De10LiteTop.v; do
    if [ ! -f "$quartus_dir/generated_verilog/$file" ]; then
      missing=1
      echo "Missing Quartus mirror input: quartus/de10_lite_qk/generated_verilog/$file"
    fi
  done
  if [ "$missing" -ne 0 ]; then
    echo "Generate the canonical HDL first with 'just spinal-generate' or your preferred SpinalHDL flow."
    exit 1
  fi
}

cmd_check() {
  quartus_setup_path || true
  echo "QUARTUS_ROOT: ${QUARTUS_ROOT:-unset}"
  local tool
  for tool in quartus_sh quartus_map quartus_fit quartus_asm quartus_pgm; do
    if path="$(quartus_find_tool "$tool")"; then
      echo "which $tool: $path"
    else
      echo "which $tool: missing"
    fi
  done
  if path="$(quartus_find_tool quartus_sh)"; then
    echo "quartus_sh --version:"
    "$path" --version || echo "quartus_sh --version failed"
  else
    echo "quartus_sh --version: unavailable because quartus_sh was not found"
  fi
  if jtagconfig="$(quartus_find_tool jtagconfig 2>/dev/null)"; then
    echo "jtagconfig:"
    "$jtagconfig" || true
  fi
  echo "USB-Blaster check: run 'quartus_pgm -l' after connecting the board and ensuring udev/permissions are configured."
}

cmd_project() {
  local quartus_sh
  require_generated_verilog
  quartus_sh="$(require_tool quartus_sh)"
  if [ ! -f "$quartus_dir/qsf/verified_de10_lite_pins.qsf" ]; then
    echo "warning: verified QSF is missing. Project will be created without board pin assignments."
  fi
  "$quartus_sh" -t "$quartus_dir/scripts/create_project.tcl"
  local qpf="$quartus_dir/de10_lite_qk.qpf"
  local qsf="$quartus_dir/de10_lite_qk.qsf"
  [ -f "$qpf" ] || { echo "Quartus project file was not created: $qpf"; exit 1; }
  [ -f "$qsf" ] || { echo "Quartus settings file was not created: $qsf"; exit 1; }
  echo "Quartus project created: $qpf"
  echo "Quartus settings file created: $qsf"
}

cmd_compile() {
  local quartus_sh
  quartus_sh="$(require_tool quartus_sh)"
  [ -f "$quartus_dir/de10_lite_qk.qpf" ] || {
    echo "Quartus project has not been created yet. Run './scripts/quartus.sh project' first."
    exit 1
  }
  [ -f "$quartus_dir/qsf/verified_de10_lite_pins.qsf" ] || {
    echo "Verified DE10-Lite QSF is missing. Import one with './scripts/quartus.sh import-qsf /path/to/verified.qsf' before compile."
    exit 1
  }
  "$quartus_sh" -t "$quartus_dir/scripts/compile.tcl"
}

cmd_program() {
  local quartus_sh
  quartus_sh="$(require_tool quartus_sh)"
  require_tool quartus_pgm >/dev/null
  check_jtag_lock || exit 1
  [ -f "$quartus_dir/output_files/de10_lite_qk.sof" ] || {
    echo "Programming file missing. Run './scripts/quartus.sh compile' after importing a verified QSF."
    exit 1
  }
  "$quartus_sh" -t "$quartus_dir/scripts/program_sof.tcl"
}

cmd_import_qsf() {
  local qsf_path="${1:-}"
  if [ -z "$qsf_path" ]; then
    echo "Missing QSF path."
    usage
    exit 1
  fi
  "$quartus_dir/scripts/import_verified_qsf.sh" "$qsf_path"
}

command="${1:-}"

case "$command" in
  check)
    cmd_check
    ;;
  project)
    cmd_project
    ;;
  compile)
    cmd_compile
    ;;
  program)
    cmd_program
    ;;
  import-qsf)
    shift || true
    cmd_import_qsf "${1:-}"
    ;;
  ""|-h|--help|help)
    usage
    ;;
  *)
    echo "Unknown command: $command"
    usage
    exit 1
    ;;
esac
