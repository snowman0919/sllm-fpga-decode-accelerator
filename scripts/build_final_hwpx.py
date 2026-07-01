#!/usr/bin/env python3
"""Build a Hancom HWPX intermediate from the final Markdown manuscript.

The repository environment cannot write legacy `.hwp` directly.  This script
uses the HWPX journal template kept next to the project and replaces its body
with the current Markdown manuscript, producing a file Hancom Office can open
and save as `.hwp`.
"""

from __future__ import annotations

import re
import shutil
import struct
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "paper" / "current" / "manuscript.md"
SRC = ROOT.parent / "paper" / "한국정보기술진흥원_논문양식.hwpx"
WORK = ROOT / "build" / "final_manuscript_hwpx"
OUT = ROOT / "paper" / "final" / "final_manuscript.hwpx"

NS = {
    "hp": "http://www.hancom.co.kr/hwpml/2011/paragraph",
    "hs": "http://www.hancom.co.kr/hwpml/2011/section",
    "hc": "http://www.hancom.co.kr/hwpml/2011/core",
}
for prefix, uri in {
    "ha": "http://www.hancom.co.kr/hwpml/2011/app",
    "hp": NS["hp"],
    "hp10": "http://www.hancom.co.kr/hwpml/2016/paragraph",
    "hs": NS["hs"],
    "hc": NS["hc"],
    "hh": "http://www.hancom.co.kr/hwpml/2011/head",
    "hhs": "http://www.hancom.co.kr/hwpml/2011/history",
    "hm": "http://www.hancom.co.kr/hwpml/2011/master-page",
    "hpf": "http://www.hancom.co.kr/schema/2011/hpf",
    "dc": "http://purl.org/dc/elements/1.1/",
    "opf": "http://www.idpf.org/2007/opf/",
    "ooxmlchart": "http://www.hancom.co.kr/hwpml/2016/ooxmlchart",
    "hwpunitchar": "http://www.hancom.co.kr/hwpml/2016/HwpUnitChar",
    "epub": "http://www.idpf.org/2007/ops",
    "config": "urn:oasis:names:tc:opendocument:xmlns:config:1.0",
}.items():
    ET.register_namespace(prefix, uri)

COLUMN_WIDTH = 22000


def q(prefix: str, tag: str) -> str:
    return f"{{{NS[prefix]}}}{tag}"


def clean_inline(text: str) -> str:
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = text.replace("**", "").replace("`", "")
    return text.strip()


def paragraph(text: str = "", char: str = "7", para: str = "0", center: bool = False) -> ET.Element:
    node = ET.Element(
        q("hp", "p"),
        {
            "id": "0",
            "paraPrIDRef": "19" if center else para,
            "styleIDRef": "0",
            "pageBreak": "0",
            "columnBreak": "0",
            "merged": "0",
        },
    )
    run = ET.SubElement(node, q("hp", "run"), {"charPrIDRef": char})
    if text:
        t = ET.SubElement(run, q("hp", "t"))
        t.text = clean_inline(text)
    return node


def column_paragraph(count: int) -> ET.Element:
    node = paragraph()
    run = node.find("hp:run", NS)
    if run is None:
        raise RuntimeError("template paragraph run missing")
    ctrl = ET.SubElement(run, q("hp", "ctrl"))
    attrs = {"id": "", "type": "NEWSPAPER", "layout": "LEFT", "colCount": str(count), "sameSz": "1"}
    attrs["sameGap"] = "2268" if count == 2 else "0"
    col = ET.SubElement(ctrl, q("hp", "colPr"), attrs)
    if count == 2:
        ET.SubElement(col, q("hp", "colLine"), {"type": "SOLID", "width": "0.12 mm", "color": "#000000"})
    return node


def parse_front(lines: list[str]) -> tuple[list[ET.Element], list[str]]:
    title_ko = lines[2].lstrip("# ").strip()
    title_en = lines[4].strip("*").strip()
    author_ko, aff_ko, author_en, aff_en = [lines[i].strip() for i in (6, 8, 10, 12)]

    def section(start_marker: str, end_marker: str) -> list[str]:
        start = lines.index(start_marker) + 1
        end = lines.index(end_marker)
        return [line for line in lines[start:end] if line.strip()]

    abstract_ko = section("## 초록", "## Abstract")
    abstract_en = section("## Abstract", "## 1. 서론")
    kw_ko = abstract_ko.pop().replace("**키워드:**", "키워드 |").strip()
    kw_en = abstract_en.pop().replace("**Keyword:**", "Keyword |").strip()

    front = [
        paragraph(title_ko, "9", "19", True),
        paragraph(title_en, "9", "19", True),
        paragraph(author_ko, "8", "19", True),
        paragraph(aff_ko, "8", "19", True),
        paragraph(author_en, "8", "19", True),
        paragraph(aff_en, "8", "19", True),
        paragraph("초      록", "10", "19", True),
        *[paragraph(line, "7") for line in abstract_ko],
        paragraph(kw_ko, "7"),
        paragraph("Abstract", "10", "19", True),
        *[paragraph(line, "7") for line in abstract_en],
        paragraph(kw_en, "7"),
    ]
    return front, lines[lines.index("## 1. 서론") :]


def parse_table(lines: list[str], start: int) -> tuple[list[list[str]], int]:
    rows: list[list[str]] = []
    i = start
    while i < len(lines) and lines[i].strip().startswith("|"):
        rows.append([clean_inline(cell) for cell in lines[i].strip().strip("|").split("|")])
        i += 1
    if len(rows) > 1 and all(re.fullmatch(r":?-{3,}:?", c.replace(" ", "")) for c in rows[1]):
        rows.pop(1)
    return rows, i


def table_paragraph(rows: list[list[str]], num: int) -> ET.Element:
    col_count = max(len(row) for row in rows)
    widths = [COLUMN_WIDTH // col_count] * col_count
    widths[-1] += COLUMN_WIDTH - sum(widths)
    row_h = 1550
    tbl = ET.Element(
        q("hp", "tbl"),
        {
            "id": str(1900000000 + num),
            "zOrder": "0",
            "numberingType": "TABLE",
            "textWrap": "TOP_AND_BOTTOM",
            "textFlow": "BOTH_SIDES",
            "lock": "0",
            "dropcapstyle": "None",
            "pageBreak": "TABLE",
            "repeatHeader": "1",
            "rowCnt": str(len(rows)),
            "colCnt": str(col_count),
            "cellSpacing": "0",
            "borderFillIDRef": "3",
            "noAdjust": "0",
        },
    )
    ET.SubElement(tbl, q("hp", "sz"), {"width": str(COLUMN_WIDTH), "widthRelTo": "ABSOLUTE", "height": str(row_h * len(rows)), "heightRelTo": "ABSOLUTE", "protect": "0"})
    ET.SubElement(tbl, q("hp", "pos"), {"treatAsChar": "0", "affectLSpacing": "0", "flowWithText": "1", "allowOverlap": "0", "holdAnchorAndSO": "0", "vertRelTo": "PARA", "horzRelTo": "COLUMN", "vertAlign": "TOP", "horzAlign": "LEFT", "vertOffset": "0", "horzOffset": "0"})
    ET.SubElement(tbl, q("hp", "outMargin"), {"left": "283", "right": "283", "top": "283", "bottom": "283"})
    ET.SubElement(tbl, q("hp", "inMargin"), {"left": "180", "right": "180", "top": "120", "bottom": "120"})
    for r_idx, row in enumerate(rows):
        tr = ET.SubElement(tbl, q("hp", "tr"))
        for c_idx in range(col_count):
            text = row[c_idx] if c_idx < len(row) else ""
            tc = ET.SubElement(tr, q("hp", "tc"), {"header": "1" if r_idx == 0 else "0", "hasMargin": "0", "protect": "0", "editable": "0", "dirty": "0", "borderFillIDRef": "3"})
            sub = ET.SubElement(tc, q("hp", "subList"), {"id": "", "textDirection": "HORIZONTAL", "lineWrap": "BREAK", "vertAlign": "CENTER", "linkListIDRef": "0", "linkListNextIDRef": "0", "textWidth": str(widths[c_idx]), "textHeight": "0", "hasTextRef": "0", "hasNumRef": "0"})
            sub.append(paragraph(text, "12" if r_idx == 0 else "7", "19" if r_idx == 0 else "0", r_idx == 0))
            ET.SubElement(tc, q("hp", "cellAddr"), {"colAddr": str(c_idx), "rowAddr": str(r_idx)})
            ET.SubElement(tc, q("hp", "cellSpan"), {"colSpan": "1", "rowSpan": "1"})
            ET.SubElement(tc, q("hp", "cellSz"), {"width": str(widths[c_idx]), "height": str(row_h)})
            ET.SubElement(tc, q("hp", "cellMargin"), {"left": "180", "right": "180", "top": "120", "bottom": "120"})
    node = paragraph()
    run = node.find("hp:run", NS)
    if run is None:
        raise RuntimeError("table paragraph run missing")
    run.insert(0, tbl)
    return node


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as f:
        sig = f.read(24)
    if sig[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"not a PNG: {path}")
    return struct.unpack(">II", sig[16:24])


def picture_paragraph(path: Path, image_id: str, num: int) -> ET.Element:
    width_px, height_px = png_size(path)
    width = COLUMN_WIDTH
    height = max(5000, int(width * height_px / width_px))
    node = paragraph()
    run = node.find("hp:run", NS)
    if run is None:
        raise RuntimeError("picture paragraph run missing")
    pic = ET.Element(q("hp", "pic"), {"id": str(1950000000 + num), "zOrder": "0", "numberingType": "PICTURE", "textWrap": "TOP_AND_BOTTOM", "textFlow": "BOTH_SIDES", "lock": "0", "dropcapstyle": "None", "href": "", "groupLevel": "0", "instid": str(700000 + num), "reverse": "0"})
    for tag, attrs in [("offset", {"x": "0", "y": "0"}), ("orgSz", {"width": str(width), "height": str(height)}), ("curSz", {"width": "0", "height": "0"}), ("flip", {"horizontal": "0", "vertical": "0"})]:
        ET.SubElement(pic, q("hp", tag), attrs)
    ET.SubElement(pic, q("hp", "rotationInfo"), {"angle": "0", "centerX": str(width // 2), "centerY": str(height // 2), "rotateimage": "1"})
    rendering = ET.SubElement(pic, q("hp", "renderingInfo"))
    for matrix in ["transMatrix", "scaMatrix", "rotMatrix"]:
        ET.SubElement(rendering, q("hc", matrix), {"e1": "1", "e2": "0", "e3": "0", "e4": "0", "e5": "1", "e6": "0"})
    rect = ET.SubElement(pic, q("hp", "imgRect"))
    ET.SubElement(rect, q("hc", "pt0"), {"x": "0", "y": "0"})
    ET.SubElement(rect, q("hc", "pt1"), {"x": str(width), "y": "0"})
    ET.SubElement(rect, q("hc", "pt2"), {"x": str(width), "y": str(height)})
    ET.SubElement(rect, q("hc", "pt3"), {"x": "0", "y": str(height)})
    ET.SubElement(pic, q("hp", "imgClip"), {"left": "0", "right": str(width), "top": "0", "bottom": str(height)})
    ET.SubElement(pic, q("hp", "inMargin"), {"left": "0", "right": "0", "top": "0", "bottom": "0"})
    ET.SubElement(pic, q("hp", "imgDim"), {"dimwidth": str(width), "dimheight": str(height)})
    ET.SubElement(pic, q("hc", "img"), {"binaryItemIDRef": image_id, "bright": "0", "contrast": "0", "effect": "REAL_PIC", "alpha": "0"})
    ET.SubElement(pic, q("hp", "effects"))
    ET.SubElement(pic, q("hp", "sz"), {"width": str(width), "widthRelTo": "ABSOLUTE", "height": str(height), "heightRelTo": "ABSOLUTE", "protect": "0"})
    ET.SubElement(pic, q("hp", "pos"), {"treatAsChar": "1", "affectLSpacing": "0", "flowWithText": "1", "allowOverlap": "0", "holdAnchorAndSO": "0", "vertRelTo": "PARA", "horzRelTo": "PARA", "vertAlign": "TOP", "horzAlign": "CENTER", "vertOffset": "0", "horzOffset": "0"})
    ET.SubElement(pic, q("hp", "outMargin"), {"left": "0", "right": "0", "top": "0", "bottom": "0"})
    comment = ET.SubElement(pic, q("hp", "shapeComment"))
    comment.text = f"그림입니다. 원본 그림의 이름: {path.name}"
    run.insert(0, pic)
    return node


def build_body(sec: ET.Element, body: list[str]) -> None:
    table_num = 1
    image_num = 1
    i = 0
    while i < len(body):
        line = body[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("|"):
            rows, i = parse_table(body, i)
            sec.append(table_paragraph(rows, table_num))
            table_num += 1
            continue
        image = re.match(r"!\[[^\]]*\]\(([^)]+)\)", line)
        if image:
            path = (ROOT / "paper" / "current" / image.group(1)).resolve()
            if not path.exists():
                path = (ROOT / image.group(1)).resolve()
            image_id = f"image{image_num}"
            shutil.copyfile(path, WORK / "BinData" / f"{image_id}.png")
            sec.append(picture_paragraph(path, image_id, image_num))
            image_num += 1
            i += 1
            continue
        heading = re.match(r"^(#{1,4})\s+(.+)", line)
        if heading:
            level, text = len(heading.group(1)), heading.group(2)
            sec.append(paragraph(text, "11" if level <= 2 else "12", "19" if level <= 2 else "0", level <= 2))
        elif line.startswith("**표 ") and line.endswith("**"):
            sec.append(paragraph(line.strip("*"), "10", "19", True))
        elif line.startswith("그림 "):
            sec.append(paragraph(line, "12", "19", True))
        else:
            sec.append(paragraph(re.sub(r"^\d+\.\s+", "", line), "7"))
        i += 1


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"HWPX template not found: {SRC}")
    lines = MD.read_text(encoding="utf-8").splitlines()
    front, body = parse_front(lines)

    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    with zipfile.ZipFile(SRC) as zf:
        zf.extractall(WORK)
    (WORK / "BinData").mkdir(exist_ok=True)

    sec_path = WORK / "Contents" / "section0.xml"
    tree = ET.parse(sec_path)
    sec = tree.getroot()
    for child in list(sec):
        sec.remove(child)
    for node in front:
        sec.append(node)
    sec.append(column_paragraph(2))
    build_body(sec, body)
    tree.write(sec_path, encoding="utf-8", xml_declaration=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        OUT.unlink()
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(WORK.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(WORK).as_posix())
    print(OUT)


if __name__ == "__main__":
    main()
