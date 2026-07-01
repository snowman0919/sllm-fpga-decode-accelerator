#!/usr/bin/env python3
"""Extract paper-facing Quartus resource and timing summaries."""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QUARTUS_DIR = PROJECT_ROOT / "quartus/de10_lite_jtag_matvec/output_files"
DEFAULT_CSV = PROJECT_ROOT / "assets/c11.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quartus-dir", default=str(DEFAULT_QUARTUS_DIR))
    parser.add_argument("--out-csv", default=str(DEFAULT_CSV))
    parser.add_argument("--out-md", default="")
    parser.add_argument("--clock-name", default="CLOCK_50")
    parser.add_argument("--clock-target-mhz", type=float, default=50.0)
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def display_path(path: Path | None, base: Path = PROJECT_ROOT) -> str:
    if path is None or not path.exists():
        return ""
    try:
        resolved = path.resolve()
    except OSError:
        resolved = path
    try:
        return str(resolved.relative_to(base.resolve()))
    except ValueError:
        return str(resolved)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean_number(text: str) -> str:
    return text.replace(",", "").strip()


def parse_used_available_percent(value: str) -> tuple[str, str, str]:
    match = re.search(r"([\d,]+)\s*/\s*([\d,]+)\s*\(\s*([^)]+?)\s*\)", value)
    if not match:
        return clean_number(value), "", ""
    return clean_number(match.group(1)), clean_number(match.group(2)), match.group(3).strip()


def fit_field(text: str, key: str) -> str:
    match = re.search(rf"^\s*{re.escape(key)}\s*:\s*(.+)$", text, re.MULTILINE)
    if match:
        return match.group(1).strip()
    match = re.search(rf";\s*{re.escape(key)}\s*;\s*(.+?)\s*;", text)
    return match.group(1).strip() if match else ""


def parse_fit_summary(text: str) -> dict[str, str]:
    fields = {
        "compile_status": fit_field(text, "Fitter Status") or fit_field(text, "Flow Status"),
        "quartus_version": fit_field(text, "Quartus Prime Version"),
        "revision_name": fit_field(text, "Revision Name"),
        "top_entity": fit_field(text, "Top-level Entity Name"),
        "family": fit_field(text, "Family"),
        "target_device": fit_field(text, "Device"),
        "timing_models": fit_field(text, "Timing Models"),
        "total_registers": clean_number(fit_field(text, "Total registers")),
    }
    resource_keys = {
        "logic_elements": "Total logic elements",
        "combinational_functions": "Total combinational functions",
        "dedicated_logic_registers": "Dedicated logic registers",
        "pins": "Total pins",
        "memory_bits": "Total memory bits",
        "dsp_9bit_elements": "Embedded Multiplier 9-bit elements",
        "plls": "Total PLLs",
    }
    for prefix, key in resource_keys.items():
        used, available, percent = parse_used_available_percent(fit_field(text, key))
        fields[f"{prefix}_used"] = used
        fields[f"{prefix}_available"] = available
        fields[f"{prefix}_percent"] = percent
    return fields


def parse_sta_summary(text: str, clock_name: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    best_setup_slacks = []
    hold_slacks = []
    for block in re.finditer(r"Type\s+:\s*(.+?)\nSlack\s+:\s*([-+]?\d+(?:\.\d+)?)\nTNS\s+:\s*([-+]?\d+(?:\.\d+)?)", text):
        typ, slack, tns = block.group(1), block.group(2), block.group(3)
        if clock_name not in typ:
            continue
        if "Setup" in typ:
            best_setup_slacks.append(float(slack))
        if "Hold" in typ:
            hold_slacks.append(float(slack))
        if "Setup" in typ and "Slow 1200mV 85C" in typ:
            fields["worst_setup_slack_ns"] = slack
            fields["setup_tns"] = tns
        if "Hold" in typ and "Fast 1200mV 0C" in typ:
            fields["worst_hold_slack_ns"] = slack
            fields["hold_tns"] = tns
    if "worst_setup_slack_ns" not in fields and best_setup_slacks:
        fields["worst_setup_slack_ns"] = f"{min(best_setup_slacks):.3f}"
    if "worst_hold_slack_ns" not in fields and hold_slacks:
        fields["worst_hold_slack_ns"] = f"{min(hold_slacks):.3f}"
    return fields


def parse_sta_rpt(text: str, clock_name: str) -> dict[str, str]:
    fmax_rows: list[tuple[float, str]] = []
    for match in re.finditer(r";\s*([\d.]+)\s+MHz\s*;\s*[\d.]+\s+MHz\s*;\s*([^;]+?)\s*;", text):
        fmax = float(match.group(1))
        clock = match.group(2).strip()
        if clock == clock_name:
            window_start = max(0, match.start() - 500)
            context = text[window_start : match.start()]
            model_match = re.search(r";\s*([^;\n]+?Model) Fmax Summary", context)
            model = model_match.group(1).strip() if model_match else ""
            fmax_rows.append((fmax, model))
    if not fmax_rows:
        return {"fmax_mhz": "", "fmax_model": ""}
    fmax, model = min(fmax_rows, key=lambda item: item[0])
    return {"fmax_mhz": f"{fmax:.3f}", "fmax_model": model}


def write_csv(path: Path, row: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


def write_md(path: Path, row: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Quartus Resource and Timing Summary",
        "",
        "This table is extracted from Quartus report files. It describes the DE10-Lite JTAG Decode MatVec primitive build only.",
        "",
        "| field | value |",
        "| --- | --- |",
    ]
    for key, value in row.items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(
        [
            "",
            "Claim boundary: this is implementation/resource/timing evidence for the fixed FPGA primitive and JTAG register path. It is not a whole-graph runtime acceleration result.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    quartus_dir = Path(args.quartus_dir).expanduser().resolve()
    fit_summary = next(quartus_dir.glob("*.fit.summary"), None)
    sta_summary = next(quartus_dir.glob("*.sta.summary"), None)
    sta_rpt = next(quartus_dir.glob("*.sta.rpt"), None)
    flow_rpt = next(quartus_dir.glob("*.flow.rpt"), None)
    sof = next(quartus_dir.glob("*.sof"), None)

    fit_text = read_text(fit_summary) if fit_summary else ""
    sta_summary_text = read_text(sta_summary) if sta_summary else ""
    sta_rpt_text = read_text(sta_rpt) if sta_rpt else ""

    row: dict[str, object] = {
        "design": "de10_lite_jtag_matvec",
        "clock_name": args.clock_name,
        "clock_target_mhz": args.clock_target_mhz,
        **parse_fit_summary(fit_text),
        **parse_sta_summary(sta_summary_text, args.clock_name),
        **parse_sta_rpt(sta_rpt_text, args.clock_name),
        "timing_met": "",
        "fit_summary": display_path(fit_summary),
        "sta_summary": display_path(sta_summary),
        "sta_rpt": display_path(sta_rpt),
        "flow_rpt": display_path(flow_rpt),
        "sof_path": display_path(sof),
        "sof_sha256": sha256(sof) if sof and sof.exists() else "",
    }
    setup = float(row["worst_setup_slack_ns"]) if row.get("worst_setup_slack_ns") not in ("", None) else None
    hold = float(row["worst_hold_slack_ns"]) if row.get("worst_hold_slack_ns") not in ("", None) else None
    row["timing_met"] = bool(setup is not None and hold is not None and setup >= 0.0 and hold >= 0.0)

    write_csv(Path(args.out_csv), row)
    if args.out_md:
        write_md(Path(args.out_md), row)
    print(f"wrote {args.out_csv}")
    if args.out_md:
        print(f"wrote {args.out_md}")


if __name__ == "__main__":
    main()
