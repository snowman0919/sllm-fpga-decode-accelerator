#!/usr/bin/env bash
set -eu -o pipefail

if [ "$#" -ne 1 ]; then
  echo "usage: $0 qsf_path=/absolute/path/to/verified_de10_lite.qsf"
  echo "   or: $0 /absolute/path/to/verified_de10_lite.qsf"
  exit 1
fi

src="$1"
src="${src#qsf_path=}"
if [ ! -f "$src" ]; then
  echo "verified QSF not found: $src"
  exit 1
fi

script_dir="$(cd "$(dirname "$0")" && pwd)"
dest_dir="$script_dir/../qsf"
dest="$dest_dir/verified_de10_lite_pins.qsf"

mkdir -p "$dest_dir"
cp "$src" "$dest"
echo "Imported verified DE10-Lite QSF to: $dest"
