#!/usr/bin/env bash

quartus_prepend_path() {
  local dir="$1"
  if [ -d "$dir" ]; then
    case ":$PATH:" in
      *":$dir:"*) ;;
      *) export PATH="$dir:$PATH" ;;
    esac
    return 0
  fi
  return 1
}

quartus_add_paths() {
  local root="$1"
  local added=1
  local dir
  local dirs=(
    "$root/quartus/bin"
    "$root/quartus/bin64"
    "$root/quartus/sopc_builder/bin"
    "$root/modelsim_ase/bin"
    "$root/questa_fse/bin"
    "$root/questa_fe/bin"
    "$root/questa_ase/bin"
  )

  for dir in "${dirs[@]}"; do
    if quartus_prepend_path "$dir"; then
      added=0
    fi
  done
  return "$added"
}

quartus_find_install_root() {
  local root
  local versioned
  local roots=(
    "/opt/intelFPGA_lite"
    "/opt/altera_lite"
    "$HOME/intelFPGA_lite"
    "$HOME/.intelFPGA_lite"
    "$HOME/altera_lite"
    "$HOME/.altera_lite"
  )

  if [ -n "${QUARTUS_ROOT:-}" ]; then
    echo "$QUARTUS_ROOT"
    return 0
  fi

  for root in "${roots[@]}"; do
    if [ -x "$root/quartus/bin/quartus_sh" ]; then
      echo "$root"
      return 0
    fi

    for versioned in "$root"/*; do
      if [ -x "$versioned/quartus/bin/quartus_sh" ]; then
        echo "$versioned"
        return 0
      fi
    done
  done

  return 1
}

quartus_setup_path() {
  local root

  if root="$(quartus_find_install_root)"; then
    export QUARTUS_ROOT="$root"
    quartus_add_paths "$QUARTUS_ROOT" || true
  fi

  command -v quartus_sh >/dev/null 2>&1
}

quartus_find_tool() {
  local tool="$1"
  quartus_setup_path >/dev/null 2>&1 || true
  command -v "$tool" 2>/dev/null || return 1
}
