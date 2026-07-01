#!/usr/bin/env python3
"""Export the current manuscript to a simple self-contained HTML review file."""

from __future__ import annotations

import html
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "paper" / "current" / "manuscript.md"
OUT_DIR = ROOT / "paper" / "final"
OUT = OUT_DIR / "final_manuscript_intermediate.html"


def inline_md(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', escaped)
    return escaped


def html_image_src(src: str) -> str:
    if src.startswith("paper_assets/"):
        return f"../../{src}"
    return src


def convert_table(lines: list[str]) -> str:
    rows = [[c.strip() for c in line.strip().strip("|").split("|")] for line in lines]
    header = rows[0]
    body = rows[2:]
    out = ["<table>", "<thead><tr>"]
    out.extend(f"<th>{inline_md(cell)}</th>" for cell in header)
    out.append("</tr></thead>")
    out.append("<tbody>")
    for row in body:
        out.append("<tr>")
        out.extend(f"<td>{inline_md(cell)}</td>" for cell in row)
        out.append("</tr>")
    out.append("</tbody></table>")
    return "\n".join(out)


def markdown_to_html(md: str) -> str:
    html_lines: list[str] = []
    paragraph: list[str] = []
    table: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            html_lines.append(f"<p>{inline_md(' '.join(paragraph))}</p>")
            paragraph.clear()

    def flush_table() -> None:
        if table:
            html_lines.append(convert_table(table))
            table.clear()

    for raw in md.splitlines():
        line = raw.rstrip()
        if line.startswith("|") and line.endswith("|"):
            flush_paragraph()
            table.append(line)
            continue
        flush_table()
        if not line:
            flush_paragraph()
            continue
        if line.startswith("![") and "](" in line and line.endswith(")"):
            flush_paragraph()
            match = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", line)
            if match:
                alt, src = match.groups()
                html_lines.append(
                    f'<figure><img src="{html.escape(html_image_src(src))}" alt="{html.escape(alt)}">'
                    f"<figcaption>{inline_md(alt)}</figcaption></figure>"
                )
            continue
        if line.startswith("#"):
            flush_paragraph()
            level = min(len(line) - len(line.lstrip("#")), 4)
            text = line[level:].strip()
            html_lines.append(f"<h{level}>{inline_md(text)}</h{level}>")
            continue
        if line.startswith("- "):
            flush_paragraph()
            html_lines.append(f"<ul><li>{inline_md(line[2:].strip())}</li></ul>")
            continue
        paragraph.append(line)

    flush_paragraph()
    flush_table()
    return "\n".join(html_lines)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    md = SRC.read_text(encoding="utf-8")
    body = markdown_to_html(md)
    doc = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>온디바이스 ONNX Runtime sLLM 추론의 Decode 병목 분석과 FPGA 기반 INT8 MatVec 가속기 구조 제안</title>
  <style>
    body {{ font-family: "Noto Sans CJK KR", "Malgun Gothic", sans-serif; line-height: 1.55; margin: 40px auto; max-width: 980px; color: #111; }}
    h1 {{ font-size: 1.75rem; margin-top: 1.6rem; }}
    h2 {{ font-size: 1.35rem; margin-top: 1.4rem; border-bottom: 1px solid #ddd; padding-bottom: .25rem; }}
    h3 {{ font-size: 1.1rem; margin-top: 1.2rem; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; font-size: .9rem; }}
    th, td {{ border: 1px solid #bbb; padding: .35rem .45rem; vertical-align: top; }}
    th {{ background: #f2f4f5; }}
    img {{ max-width: 100%; height: auto; }}
    figure {{ margin: 1rem 0; }}
    figcaption {{ font-size: .9rem; color: #444; }}
    code {{ font-family: "D2Coding", monospace; font-size: .92em; }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""
    OUT.write_text(doc, encoding="utf-8")
    (OUT_DIR / "final_manuscript_intermediate.md").write_text(md, encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
