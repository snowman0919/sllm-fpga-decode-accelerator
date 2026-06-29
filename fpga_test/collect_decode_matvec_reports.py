#!/usr/bin/env python3
"""Collect resource and timing summaries for the Decode MatVec Quartus demo."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


RESOURCE_RE = re.compile(r"^(?P<metric>[^:]+)\s+:\s+(?P<used>[\d,]+)\s*/\s*(?P<total>[\d,]+)\s*\(\s*(?P<percent><\s*1|\d+)\s*%\s*\)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quartus-dir", default="quartus/de10_lite_decode_matvec")
    parser.add_argument("--tables-dir", default="paper_assets/tables")
    return parser.parse_args()


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def parse_resources(quartus_dir: Path) -> list[dict[str, object]]:
    summary = quartus_dir / "output_files" / "de10_lite_decode_matvec.fit.summary"
    if not summary.exists():
        summary = quartus_dir / "de10_lite_decode_matvec.fit.summary"
    rows: list[dict[str, object]] = []
    if not summary.exists():
        return [{
            "metric": "compile_status",
            "used": "",
            "total": "",
            "percent": "",
            "status": "missing_fit_summary",
            "source": str(summary),
        }]
    for line in summary.read_text(errors="replace").splitlines():
        match = RESOURCE_RE.match(line.strip())
        if not match:
            continue
        rows.append({
            "metric": match.group("metric").strip(),
            "used": match.group("used").replace(",", ""),
            "total": match.group("total").replace(",", ""),
            "percent": match.group("percent").replace(" ", ""),
            "status": "reported",
            "source": str(summary),
        })
    return rows or [{
        "metric": "compile_status",
        "used": "",
        "total": "",
        "percent": "",
        "status": "no_resource_rows_found",
        "source": str(summary),
    }]


def parse_timing(quartus_dir: Path) -> list[dict[str, object]]:
    summary = quartus_dir / "output_files" / "de10_lite_decode_matvec.sta.summary"
    if not summary.exists():
        summary = quartus_dir / "de10_lite_decode_matvec.sta.summary"
    if not summary.exists():
        return [{
            "corner_type": "compile_status",
            "slack": "",
            "tns": "",
            "status": "missing_sta_summary",
            "source": str(summary),
        }]

    rows: list[dict[str, object]] = []
    current_type = None
    current_slack = None
    current_tns = None
    for line in summary.read_text(errors="replace").splitlines():
        stripped = line.strip()
        if stripped.startswith("Type"):
            if current_type is not None:
                rows.append({
                    "corner_type": current_type,
                    "slack": current_slack,
                    "tns": current_tns,
                    "status": "reported",
                    "source": str(summary),
                })
            current_type = stripped.split(":", 1)[1].strip()
            current_slack = None
            current_tns = None
        elif stripped.startswith("Slack") and current_type is not None:
            current_slack = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("TNS") and current_type is not None:
            current_tns = stripped.split(":", 1)[1].strip()
    if current_type is not None:
        rows.append({
            "corner_type": current_type,
            "slack": current_slack,
            "tns": current_tns,
            "status": "reported",
            "source": str(summary),
        })
    return rows or [{
        "corner_type": "compile_status",
        "slack": "",
        "tns": "",
        "status": "no_timing_rows_found",
        "source": str(summary),
    }]


def main() -> None:
    args = parse_args()
    quartus_dir = Path(args.quartus_dir)
    tables_dir = Path(args.tables_dir)
    write_csv(tables_dir / "decode_matvec_fpga_resource.csv", parse_resources(quartus_dir))
    write_csv(tables_dir / "decode_matvec_fpga_timing.csv", parse_timing(quartus_dir))


if __name__ == "__main__":
    main()
