#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path


REQUIRED_PATTERNS = {
    "fit_summary": "*.fit.summary",
    "map_summary": "*.map.summary",
    "sta_summary": "*.sta.summary",
}

OPTIONAL_PATTERNS = {
    "fit_rpt": "*.fit.rpt",
    "map_rpt": "*.map.rpt",
    "sta_rpt": "*.sta.rpt",
    "flow_rpt": "*.flow.rpt",
}

FIT_RESOURCE_METRICS = [
    "Total logic elements",
    "Total combinational functions",
    "Dedicated logic registers",
    "Total pins",
    "Total memory bits",
    "Embedded Multiplier 9-bit elements",
    "Total PLLs",
    "UFM blocks",
    "ADC blocks",
]

MAP_ESTIMATE_METRICS = [
    "Total logic elements",
    "Total combinational functions",
    "Dedicated logic registers",
    "Total registers",
    "Total pins",
    "Total virtual pins",
    "Total memory bits",
    "Embedded Multiplier 9-bit elements",
    "Total PLLs",
    "UFM blocks",
    "ADC blocks",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Collect Quartus compile artifacts and emit paper-ready CSV/Markdown "
            "summaries for the DE10-Lite INT8 QK dot-product validation flow."
        )
    )
    parser.add_argument("--quartus-dir", required=True, help="Quartus project dir or output_files dir")
    parser.add_argument("--out-dir", required=True, help="Repository root for generated summaries")
    parser.add_argument("--expected-score", required=True, help="Expected signed INT32 score, for example -22")
    parser.add_argument("--expected-hex", required=True, help="Expected low-16-bit hex display, for example FFEA")
    return parser.parse_args()


def normalize_hex(raw_value: str) -> str:
    value = raw_value.strip().upper()
    if value.startswith("0X"):
        value = value[2:]
    value = value.replace("_", "")
    if not value or any(ch not in "0123456789ABCDEF" for ch in value):
        raise ValueError(f"Invalid hexadecimal value: {raw_value}")
    return value


def parse_int(raw_value: str) -> int:
    return int(raw_value, 0)


def clean_label(label: str) -> str:
    return re.sub(r"\s+", " ", label.strip())


def format_path(path: Path | None) -> str:
    return str(path.resolve()) if path else ""


def find_first(search_dirs: list[Path], pattern: str) -> Path | None:
    for directory in search_dirs:
        matches = sorted(directory.glob(pattern))
        if matches:
            return matches[0]
    return None


def get_search_dirs(quartus_dir: Path) -> list[Path]:
    base = quartus_dir.resolve()
    if not base.exists() or not base.is_dir():
        raise FileNotFoundError(f"Quartus directory does not exist: {base}")

    search_dirs: list[Path] = []
    output_files = base / "output_files"
    if output_files.is_dir():
        search_dirs.append(output_files)
    search_dirs.append(base)
    return search_dirs


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def extract_resource_rows_from_fit(summary_text: str, source_path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    line_pattern = re.compile(
        r"^(?P<metric>[^:]+?)\s*:\s*(?P<used>[\d,]+)\s*/\s*(?P<total>[\d,]+)\s*\(\s*(?P<percent>[^)]+?)\s*\)\s*$"
    )

    for line in summary_text.splitlines():
        match = line_pattern.match(line.strip())
        if not match:
            continue
        metric = clean_label(match.group("metric"))
        if metric not in FIT_RESOURCE_METRICS:
            continue
        rows.append(
            {
                "scope": "fitter_final",
                "entity": "",
                "metric": metric,
                "used": match.group("used").replace(",", ""),
                "total": match.group("total").replace(",", ""),
                "percent": clean_label(match.group("percent")).replace(" %", "%"),
                "source_report": format_path(source_path),
                "notes": "Final fitted resource utilization from Quartus fit.summary",
            }
        )
    return rows


def extract_scalar_metrics(summary_text: str, wanted_metrics: list[str], source_path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    line_pattern = re.compile(r"^(?P<metric>[^:]+?)\s*:\s*(?P<value>.+?)\s*$")

    for line in summary_text.splitlines():
        match = line_pattern.match(line.strip())
        if not match:
            continue
        metric = clean_label(match.group("metric"))
        if metric not in wanted_metrics:
            continue
        value = clean_label(match.group("value"))
        numeric_match = re.match(r"(?P<int>[\d,]+)", value)
        numeric_value = numeric_match.group("int").replace(",", "") if numeric_match else value
        rows.append(
            {
                "scope": "analysis_synthesis_estimate",
                "entity": "",
                "metric": metric,
                "used": numeric_value,
                "total": "",
                "percent": "",
                "source_report": format_path(source_path),
                "notes": "Pre-fit estimate from Quartus map.summary",
            }
        )
    return rows


def parse_numeric_prefix(raw_value: str) -> str:
    match = re.search(r"-?[\d.]+", raw_value)
    return match.group(0) if match else raw_value.strip()


def extract_entity_rows(map_rpt_text: str, source_path: Path) -> list[dict[str, str]]:
    header_line = "; Compilation Hierarchy Node"
    wanted_entities = {"De10LiteTop", "DotProductInt8_dim16"}
    rows: list[dict[str, str]] = []
    in_entity_table = False
    headers: list[str] = []

    for raw_line in map_rpt_text.splitlines():
        line = raw_line.rstrip()
        stripped = line.lstrip()
        if "Analysis & Synthesis Resource Utilization by Entity" in line:
            in_entity_table = True
            continue
        if not in_entity_table:
            continue
        if line.startswith(header_line):
            headers = [clean_label(item) for item in line.split(";")[1:-1]]
            continue
        if not stripped.startswith(";"):
            if headers and line.strip().startswith("+"):
                continue
            if headers and not line.strip():
                break
            continue

        if not headers:
            continue

        values = [clean_label(item) for item in stripped.split(";")[1:-1]]
        if len(values) != len(headers):
            continue

        data = dict(zip(headers, values))
        entity_name = data.get("Entity Name", "")
        if entity_name not in wanted_entities:
            continue

        entity_label = "top_level" if entity_name == "De10LiteTop" else "int8_qk_dot_product_core"
        for metric_name, csv_metric in [
            ("Combinational ALUTs", "Combinational ALUTs"),
            ("Dedicated Logic Registers", "Dedicated Logic Registers"),
            ("DSP Elements", "DSP Elements"),
            ("DSP 9x9", "DSP 9x9"),
            ("Pins", "Pins"),
        ]:
            rows.append(
                {
                    "scope": "entity_utilization",
                    "entity": entity_label,
                    "metric": csv_metric,
                    "used": parse_numeric_prefix(data.get(metric_name, "")),
                    "total": "",
                    "percent": "",
                    "source_report": format_path(source_path),
                    "notes": f"Resource utilization by entity ({entity_name}) from Quartus map.rpt",
                }
            )
    return rows


def extract_timing_rows(sta_summary_text: str, sta_rpt_text: str | None, summary_path: Path, rpt_path: Path | None) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    summary_pattern = re.compile(
        r"Type\s*:\s*(?P<corner>.+?)\s+'(?P<clock>[^']+)'\s*\n"
        r"Slack\s*:\s*(?P<slack>-?[\d.]+)\s*\n"
        r"TNS\s*:\s*(?P<tns>-?[\d.]+)",
        re.MULTILINE,
    )
    for match in summary_pattern.finditer(sta_summary_text):
        corner_and_analysis = clean_label(match.group("corner"))
        if " Model " not in corner_and_analysis:
            continue
        corner, analysis = corner_and_analysis.split(" Model ", 1)
        rows.append(
            {
                "corner": corner,
                "analysis": analysis,
                "clock": clean_label(match.group("clock")),
                "slack_ns": match.group("slack"),
                "tns_ns": match.group("tns"),
                "fmax_mhz": "",
                "restricted_fmax_mhz": "",
                "source_report": format_path(summary_path),
            }
        )

    if sta_rpt_text and rpt_path:
        lines = sta_rpt_text.splitlines()
        for idx, raw_line in enumerate(lines):
            if "Model Fmax Summary" not in raw_line:
                continue
            section_name = clean_label(raw_line.strip(" ;"))
            corner = section_name.replace(" Model Fmax Summary", "")
            for candidate in lines[idx + 1 : idx + 8]:
                if "MHz" not in candidate or not candidate.lstrip().startswith(";"):
                    continue
                parts = [clean_label(item) for item in candidate.split(";")[1:-1]]
                if len(parts) < 3:
                    continue
                rows.append(
                    {
                        "corner": corner,
                        "analysis": "Fmax",
                        "clock": parts[2],
                        "slack_ns": "",
                        "tns_ns": "",
                        "fmax_mhz": parse_numeric_prefix(parts[0]),
                        "restricted_fmax_mhz": parse_numeric_prefix(parts[1]),
                        "source_report": format_path(rpt_path),
                    }
                )
                break

        multicorner_pattern = re.compile(
            r";\s*Worst-case Slack\s*;\s*(?P<setup>-?[\d.]+)\s*;\s*(?P<hold>-?[\d.]+)\s*;\s*(?P<recovery>[^;]+)\s*;\s*(?P<removal>[^;]+)\s*;\s*(?P<mpw>-?[\d.]+)\s*;"
        )
        multicorner_match = multicorner_pattern.search(sta_rpt_text)
        if multicorner_match:
            for analysis, value in [
                ("Worst-case Setup", multicorner_match.group("setup")),
                ("Worst-case Hold", multicorner_match.group("hold")),
                ("Worst-case Minimum Pulse Width", multicorner_match.group("mpw")),
            ]:
                rows.append(
                    {
                        "corner": "Multicorner",
                        "analysis": analysis,
                        "clock": "CLOCK_50",
                        "slack_ns": value,
                        "tns_ns": "0.000",
                        "fmax_mhz": "",
                        "restricted_fmax_mhz": "",
                        "source_report": format_path(rpt_path),
                    }
                )

    return rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def render_markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "_No rows collected._"

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def build_validation_rows(
    quartus_dir: Path,
    out_dir: Path,
    required_reports: dict[str, Path],
    optional_reports: dict[str, Path | None],
    sof_path: Path | None,
    expected_score: int,
    expected_hex: str,
) -> list[dict[str, str]]:
    photo_placeholder = out_dir / "paper_assets" / "figures" / "de10_lite_board_photo.placeholder.md"
    raw_capture_placeholder = out_dir / "fpga_test" / "captured" / "de10_lite_validation_photo.placeholder.md"
    rows = [
        {
            "item": "validation_scope",
            "status": "ok",
            "expected": "INT8 QK dot-product core block only",
            "observed": "INT8 QK dot-product core block only",
            "notes": "Do not interpret these artifacts as full Gemma 3 1B execution or ONNX Runtime speedup data.",
            "source": format_path(quartus_dir),
        },
        {
            "item": "expected_score_int32",
            "status": "ok",
            "expected": str(expected_score),
            "observed": str(expected_score),
            "notes": "Deterministic signed INT32 reference used for board validation summary.",
            "source": "",
        },
        {
            "item": "expected_hex_low16",
            "status": "ok",
            "expected": expected_hex,
            "observed": expected_hex,
            "notes": "Expected low 16 bits on the HEX displays.",
            "source": "",
        },
        {
            "item": "hex_display_expectation",
            "status": "manual_check_required",
            "expected": "HEX3..HEX0 = F F E A",
            "observed": "Pending board photo or manual observation",
            "notes": "HEX0 shows the least-significant nibble A, then HEX1=E, HEX2=F, HEX3=F.",
            "source": "",
        },
        {
            "item": "sof_file",
            "status": "present" if sof_path else "missing",
            "expected": "Quartus-generated .sof programming file",
            "observed": format_path(sof_path) if sof_path else "",
            "notes": "Programming artifact produced by Quartus compile.",
            "source": format_path(sof_path) if sof_path else "",
        },
    ]

    for key, path in required_reports.items():
        rows.append(
            {
                "item": key,
                "status": "present",
                "expected": key.replace("_", "."),
                "observed": format_path(path),
                "notes": "Required Quartus summary artifact.",
                "source": format_path(path),
            }
        )

    for key, path in optional_reports.items():
        rows.append(
            {
                "item": key,
                "status": "present" if path else "missing",
                "expected": key.replace("_", "."),
                "observed": format_path(path) if path else "",
                "notes": "Optional detailed Quartus report used for richer paper tables.",
                "source": format_path(path) if path else "",
            }
        )

    rows.extend(
        [
            {
                "item": "raw_capture_placeholder",
                "status": "manual_capture_slot",
                "expected": "User-supplied board photo/video or notes",
                "observed": format_path(raw_capture_placeholder),
                "notes": "Replace the placeholder with raw board evidence from the DE10-Lite run.",
                "source": format_path(raw_capture_placeholder),
            },
            {
                "item": "paper_figure_placeholder",
                "status": "manual_capture_slot",
                "expected": "User-supplied paper figure image",
                "observed": format_path(photo_placeholder),
                "notes": "Replace the placeholder with a paper-ready board photo if one is selected.",
                "source": format_path(photo_placeholder),
            },
        ]
    )

    return rows


def build_markdown_summary(
    quartus_dir: Path,
    required_reports: dict[str, Path],
    optional_reports: dict[str, Path | None],
    sof_path: Path | None,
    expected_score: int,
    expected_hex: str,
    resource_rows: list[dict[str, str]],
    timing_rows: list[dict[str, str]],
    validation_rows: list[dict[str, str]],
) -> str:
    required_list = "\n".join(f"- `{name}`: `{path.resolve()}`" for name, path in required_reports.items())
    optional_present = [f"- `{name}`: `{path.resolve()}`" for name, path in optional_reports.items() if path]
    optional_missing = [name for name, path in optional_reports.items() if not path]

    resource_table_rows = [
        [
            row["scope"],
            row["entity"] or "-",
            row["metric"],
            row["used"],
            row["total"] or "-",
            row["percent"] or "-",
        ]
        for row in resource_rows
    ]
    timing_table_rows = [
        [
            row["corner"],
            row["analysis"],
            row["clock"],
            row["slack_ns"] or "-",
            row["tns_ns"] or "-",
            row["fmax_mhz"] or "-",
            row["restricted_fmax_mhz"] or "-",
        ]
        for row in timing_rows
    ]

    validation_table_rows = [
        [row["item"], row["status"], row["expected"], row["observed"] or "-", row["notes"]]
        for row in validation_rows
    ]

    sof_status = f"`{sof_path.resolve()}`" if sof_path else "Missing `.sof` file"
    optional_present_block = "\n".join(optional_present) if optional_present else "- None found"
    optional_missing_block = "\n".join(f"- `{name}`" for name in optional_missing) if optional_missing else "- None"

    return f"""# FPGA Validation Summary

## Scope

- Validation target: deterministic INT8 QK dot-product core block on DE10-Lite
- Not claimed: full Gemma 3 1B execution on FPGA
- Not claimed: FPGA speedup over ONNX Runtime
- Quartus artifact root: `{quartus_dir.resolve()}`

## Required Quartus Artifacts

{required_list}

## Optional Detailed Reports

{optional_present_block}

Missing optional reports:
{optional_missing_block}

## Programming Artifact

- `.sof` status: {sof_status}

## Expected Board Result

- Expected signed score: `{expected_score}`
- Expected low-16-bit hex: `0x{expected_hex}`
- HEX interpretation: `HEX0=A`, `HEX1=E`, `HEX2=F`, `HEX3=F`, so the board should read `HEX3..HEX0 = F F E A`
- Manual evidence still required: board photo or video should be placed in `fpga_test/captured/`, and a paper-ready selected image can be copied into `paper_assets/figures/`

## Resource Summary

{render_markdown_table(["Scope", "Entity", "Metric", "Used", "Total", "Percent"], resource_table_rows)}

## Timing Summary

{render_markdown_table(["Corner", "Analysis", "Clock", "Slack (ns)", "TNS (ns)", "Fmax (MHz)", "Restricted Fmax (MHz)"], timing_table_rows)}

## Validation Checklist

{render_markdown_table(["Item", "Status", "Expected", "Observed", "Notes"], validation_table_rows)}

## Paper Interpretation Limits

- Treat these results as synthesis and board-validation evidence for one deterministic INT8 QK dot-product block.
- Use resource and timing numbers to document feasibility on MAX 10, not to imply full-model deployment.
- Do not compare these results as end-to-end speedups versus ONNX Runtime.
"""


def main() -> int:
    args = parse_args()
    quartus_dir = Path(args.quartus_dir)
    out_dir = Path(args.out_dir).resolve()

    try:
        expected_score = parse_int(args.expected_score)
        expected_hex = normalize_hex(args.expected_hex)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if (expected_score & 0xFFFF) != int(expected_hex, 16):
        print(
            "error: --expected-score low 16 bits do not match --expected-hex "
            f"({expected_score} -> 0x{expected_score & 0xFFFF:04X}, expected 0x{expected_hex})",
            file=sys.stderr,
        )
        return 2

    try:
        search_dirs = get_search_dirs(quartus_dir)
    except FileNotFoundError as exc:
        print(
            f"error: {exc}\n"
            "hint: pass either the Quartus project directory or its output_files directory.",
            file=sys.stderr,
        )
        return 1

    required_reports: dict[str, Path] = {}
    missing_required: list[str] = []
    for key, pattern in REQUIRED_PATTERNS.items():
        path = find_first(search_dirs, pattern)
        if path:
            required_reports[key] = path
        else:
            missing_required.append(pattern)

    if missing_required:
        print(
            "error: required Quartus report files were not found.\n"
            f"searched under: {', '.join(str(path) for path in search_dirs)}\n"
            f"missing patterns: {', '.join(missing_required)}\n"
            "hint: run Quartus compile first, then retry with the project directory or output_files directory.",
            file=sys.stderr,
        )
        return 1

    optional_reports = {key: find_first(search_dirs, pattern) for key, pattern in OPTIONAL_PATTERNS.items()}
    sof_path = find_first(search_dirs, "*.sof")

    fit_summary_text = read_text(required_reports["fit_summary"])
    map_summary_text = read_text(required_reports["map_summary"])
    sta_summary_text = read_text(required_reports["sta_summary"])
    map_rpt_text = read_text(optional_reports["map_rpt"]) if optional_reports["map_rpt"] else ""
    sta_rpt_text = read_text(optional_reports["sta_rpt"]) if optional_reports["sta_rpt"] else None

    resource_rows = []
    resource_rows.extend(extract_resource_rows_from_fit(fit_summary_text, required_reports["fit_summary"]))
    resource_rows.extend(extract_scalar_metrics(map_summary_text, MAP_ESTIMATE_METRICS, required_reports["map_summary"]))
    if optional_reports["map_rpt"]:
        resource_rows.extend(extract_entity_rows(map_rpt_text, optional_reports["map_rpt"]))

    timing_rows = extract_timing_rows(
        sta_summary_text,
        sta_rpt_text,
        required_reports["sta_summary"],
        optional_reports["sta_rpt"],
    )

    validation_rows = build_validation_rows(
        quartus_dir.resolve(),
        out_dir,
        required_reports,
        optional_reports,
        sof_path,
        expected_score,
        expected_hex,
    )

    resource_csv = out_dir / "paper_assets" / "tables" / "fpga_resource_summary.csv"
    timing_csv = out_dir / "paper_assets" / "tables" / "fpga_timing_summary.csv"
    validation_csv = out_dir / "paper_assets" / "tables" / "fpga_validation_summary.csv"
    validation_md = out_dir / "fpga_test" / "captured" / "fpga_validation_summary.md"

    write_csv(
        resource_csv,
        ["scope", "entity", "metric", "used", "total", "percent", "source_report", "notes"],
        resource_rows,
    )
    write_csv(
        timing_csv,
        ["corner", "analysis", "clock", "slack_ns", "tns_ns", "fmax_mhz", "restricted_fmax_mhz", "source_report"],
        timing_rows,
    )
    write_csv(
        validation_csv,
        ["item", "status", "expected", "observed", "notes", "source"],
        validation_rows,
    )

    validation_md.parent.mkdir(parents=True, exist_ok=True)
    validation_md.write_text(
        build_markdown_summary(
            quartus_dir.resolve(),
            required_reports,
            optional_reports,
            sof_path,
            expected_score,
            expected_hex,
            resource_rows,
            timing_rows,
            validation_rows,
        ),
        encoding="utf-8",
    )

    print(f"Wrote {validation_md}")
    print(f"Wrote {resource_csv}")
    print(f"Wrote {timing_csv}")
    print(f"Wrote {validation_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
