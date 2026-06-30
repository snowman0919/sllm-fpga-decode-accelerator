#!/usr/bin/env python3
"""Build the generated reviewer package under dist/ai_accel_paper."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


INCLUDE_PATHS = [
    "README.md",
    "paper/README.md",
    "paper/current/manuscript.md",
    "windows",
    "onnx_micrographs",
    "docs/01_실험_근거와_주장_범위.md",
    "docs/02_재현_가이드.md",
    "docs/03_저장소_구조.md",
    "scripts/extract_quartus_summary.py",
    "scripts/regenerate_fpga_optimized_estimate.py",
    "scripts/build_ort_fpga_comparison.py",
    "scripts/verify_dist_package.py",
    "assets",
    "quartus/de10_lite_jtag_matvec",
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
        ignore = shutil.ignore_patterns(
            "__pycache__",
            "*.pyc",
            ".pytest_cache",
            "db",
            "incremental_db",
            "*.sopcinfo",
            "jtag_matvec_system.qsys",
            "jtag_matvec_system",
            "*.smsg",
            "*.pin",
            "*.done",
            "*.jdi",
            "*.pof",
            "*.sld",
        )
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

This generated package contains the Windows CPU/ONNX Runtime baselines, JTAG
validation runner, ONNX micrograph artifacts, claim-boundary notes, paper-facing
tables, figures, and Quartus rebuild inputs prepared from the repository.

Run locally:

```powershell
python install.py --local . --run-cpu --run-ort
```

Run strict non-hardware smoke checks:

```powershell
python install.py --local . --run-cpu --run-ort --extract-quartus-summary --strict
```

Run the optional ONNX Runtime integer micrograph baseline:

```powershell
python install.py --local . --run-ort-integer
```

Run optional USB-Blaster JTAG register validation:

```powershell
python install.py --local . --run-jtag --cable "USB-Blaster [USB-0]"
```

Require a real passing JTAG hardware run:

```powershell
python install.py --local . --run-jtag --require-jtag-pass
```

Extract packaged Quartus resource/timing summaries and rebuild the comparison table:

```powershell
python install.py --local . --extract-quartus-summary --run-full-eval
```

The JTAG path is a correctness and cycle-counter validation route. JTAG total
latency is System Console/JTAG host-tool invocation overhead, not FPGA compute
latency. The package does not claim full Gemma FPGA execution or end-to-end
ONNX Runtime speedup. The full-eval option preserves failed or skipped hardware
runs instead of converting them into passing measurements.
"""
    path.write_text(text, encoding="utf-8")


def prune_jtag_quartus_outputs(out_dir: Path) -> None:
    project_dir = out_dir / "quartus/de10_lite_jtag_matvec"
    for name in ["jtag_matvec_system.sopcinfo"]:
        path = project_dir / name
        if path.exists():
            path.unlink()
    output_dir = project_dir / "output_files"
    keep = {
        "de10_lite_jtag_matvec.sof",
        "de10_lite_jtag_matvec.fit.summary",
        "de10_lite_jtag_matvec.sta.summary",
        "de10_lite_jtag_matvec.fit.rpt",
        "de10_lite_jtag_matvec.sta.rpt",
        "de10_lite_jtag_matvec.flow.rpt",
    }
    if output_dir.exists():
        for path in output_dir.iterdir():
            if path.name not in keep:
                path.unlink()


def main() -> None:
    args = parse_args()
    out_dir = ROOT / args.out_dir
    install_src = ROOT / "scripts/dist_install.py"
    install_text = install_src.read_text(encoding="utf-8")
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for rel in INCLUDE_PATHS:
        copy_path(ROOT / rel, out_dir / rel)
    bitstream = ROOT / "quartus/de10_lite_jtag_matvec/output_files/de10_lite_jtag_matvec.sof"
    copy_path(bitstream, out_dir / "quartus/de10_lite_jtag_matvec/output_files/de10_lite_jtag_matvec.sof")
    prune_jtag_quartus_outputs(out_dir)
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
    bad = []
    for item in files:
        path = out_dir / item["path"]
        if not path.exists():
            bad.append((item["path"], "missing"))
            continue
        digest = sha256(path)
        if digest != item["sha256"]:
            bad.append((item["path"], digest, item["sha256"]))
    if bad:
        raise SystemExit(f"manifest self-test failed: {bad}")
    print(f"built {out_dir}")


if __name__ == "__main__":
    main()
