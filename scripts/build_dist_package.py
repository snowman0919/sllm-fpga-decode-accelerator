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
    "docs/windows_board_runbook.md",
    "docs/linux_windows_fpga_eval_workflow.md",
    "docs/quartus_clean_rebuild_notes.md",
    "docs/de10_lite_uart_wiring.md",
    "docs/fpga_uart_benchmark_report.md",
    "docs/fpga_jtag_benchmark_report.md",
    "docs/fpga_optimized_interface_model.md",
    "docs/jtag_matvec_offload.md",
    "docs/onnx_vs_fpga_eval_protocol.md",
    "docs/quartus_resource_timing_summary.md",
    "docs/ort_vs_fpga_comparison_interpretation.md",
    "docs/release_hygiene.md",
    "docs/ftp_upload_plan.md",
    "docs/claim_boundary.md",
    "docs/gemma_partial_offload_plan.md",
    "docs/gemma_onnx_patch_notes.md",
    "scripts/extract_quartus_summary.py",
    "scripts/regenerate_fpga_optimized_estimate.py",
    "scripts/build_ort_fpga_comparison.py",
    "scripts/verify_dist_package.py",
    "paper_assets/tables",
    "paper_assets/figures/figure_index.md",
    "paper_assets/figures/figure_index.csv",
    "paper_assets/figures/jtag_vs_optimized_fpga_latency_interpretation.png",
    "paper_assets/figures/ort_vs_fpga_latency_decomposition.png",
    "quartus/de10_lite_uart_matvec/README.md",
    "quartus/de10_lite_uart_matvec/qsf",
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
            "*.qpf",
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

This package contains the Windows CPU/ONNX Runtime baselines, optional FPGA UART
and JTAG validation runners, ONNX micrograph artifacts, claim-boundary notes, and
paper-facing tables prepared from the repository.

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

List serial ports:

```powershell
python install.py --local . --list-ports
```

Run optional FPGA UART validation:

```powershell
python install.py --local . --run-fpga --port COM5 --baud 115200
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

The FPGA UART path is a low-speed validation/control path. It is not a full
Gemma ONNX execution path and does not imply end-to-end speedup. The JTAG path
is now the preferred no-external-UART board validation route, but it is also a
correctness/overhead validation path rather than a performance interface unless
a real passing cycle-counter board log is archived. The full-eval option
preserves failed or skipped hardware runs instead of converting them into
passing measurements.
"""
    path.write_text(text, encoding="utf-8")


def prune_jtag_quartus_outputs(out_dir: Path) -> None:
    project_dir = out_dir / "quartus/de10_lite_jtag_matvec"
    for name in ["de10_lite_jtag_matvec.qpf", "de10_lite_jtag_matvec.qsf", "jtag_matvec_system.sopcinfo"]:
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
    install_src = ROOT / "dist/ai_accel_paper/install.py"
    install_text = install_src.read_text(encoding="utf-8") if install_src.exists() else ""
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for rel in INCLUDE_PATHS:
        copy_path(ROOT / rel, out_dir / rel)
    bitstream = ROOT / "quartus/de10_lite_jtag_matvec/output_files/de10_lite_jtag_matvec.sof"
    copy_path(bitstream, out_dir / "quartus/de10_lite_jtag_matvec/output_files/de10_lite_jtag_matvec.sof")
    prune_jtag_quartus_outputs(out_dir)
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
