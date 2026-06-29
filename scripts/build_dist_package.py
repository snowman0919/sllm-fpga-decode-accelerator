#!/usr/bin/env python3
"""Build a local FTP-ready package under dist/ai_accel_paper."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


INCLUDE_PATHS = [
    "windows",
    "onnx_micrographs",
    "onnx_custom_op",
    "docs/uart_protocol.md",
    "docs/windows_test_guide.md",
    "docs/ftp_upload_plan.md",
    "docs/claim_boundary.md",
    "docs/gemma_partial_offload_plan.md",
    "docs/gemma_onnx_patch_notes.md",
    "paper_assets/tables",
    "paper_assets/figures/figure_index.md",
    "paper_assets/figures/figure_index.csv",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default="dist/ai_accel_paper")
    return parser.parse_args()


def copy_path(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    if src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        ignore = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache")
        shutil.copytree(src, dst, ignore=ignore)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_readme(path: Path) -> None:
    text = """# ai_accel_paper Test Package

This package contains the Windows CPU/ONNX Runtime baselines, optional FPGA UART
validation runner, ONNX micrograph artifacts, claim-boundary notes, and
paper-facing tables prepared from the repository.

Run locally:

```powershell
python install.py --local . --run-cpu --run-ort
```

Run optional FPGA UART validation:

```powershell
python install.py --local . --run-fpga --port COM5 --baud 115200
```

The FPGA UART path is a low-speed validation/control path. It is not a full
Gemma ONNX execution path and does not imply end-to-end speedup.
"""
    path.write_text(text, encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = ROOT / args.out_dir
    install_src = ROOT / "dist/ai_accel_paper/install.py"
    install_text = install_src.read_text(encoding="utf-8") if install_src.exists() else ""
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for rel in INCLUDE_PATHS:
        copy_path(ROOT / rel, out_dir / rel)
    if install_text:
        (out_dir / "install.py").write_text(install_text, encoding="utf-8")
    write_readme(out_dir / "README.md")

    files = []
    checksum_lines = []
    for path in sorted(p for p in out_dir.rglob("*") if p.is_file()):
        if path.name in {"manifest.json", "checksums.sha256"}:
            continue
        rel = path.relative_to(out_dir).as_posix()
        digest = sha256(path)
        files.append({"path": rel, "sha256": digest, "bytes": path.stat().st_size})
        checksum_lines.append(f"{digest}  {rel}")

    manifest = {
        "package": "ai_accel_paper",
        "claim_boundary": "partial primitive and micrograph validation package; no full Gemma ONNX FPGA execution claim",
        "files": files,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out_dir / "checksums.sha256").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    print(f"built {out_dir}")


if __name__ == "__main__":
    main()
