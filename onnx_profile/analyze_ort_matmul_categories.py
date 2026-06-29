#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_MODEL = Path("/home/monad/develop/ai_accel/gemma3-1B-onnx/model.onnx")
DEFAULT_SWEEP_RAW = Path("onnx_profile/results_onnx_sweep/raw/ort_sweep_raw_runs.json")
DEFAULT_GRAPH_INSPECTION = Path("onnx_profile/results_onnx/raw/onnx_graph_inspection.json")
DEFAULT_TABLES_DIR = Path("paper_assets/tables")
DEFAULT_FIGURES_DIR = Path("paper_assets/figures")
DEFAULT_REPORT = Path("onnx_profile/results/reports/ort_matmul_hotspot_analysis.md")

CATEGORIES = [
    "attention_qkv_projection",
    "attention_qk_score",
    "attention_v_weighted_sum",
    "attention_output_projection",
    "mlp_projection",
    "lm_head",
    "unknown",
]

CATEGORY_COLORS = {
    "attention_qkv_projection": "#4477AA",
    "attention_qk_score": "#EE6677",
    "attention_v_weighted_sum": "#228833",
    "attention_output_projection": "#CCBB44",
    "mlp_projection": "#66CCEE",
    "lm_head": "#AA3377",
    "unknown": "#BBBBBB",
}


@dataclass(frozen=True)
class GraphNode:
    index: int
    name: str
    op_type: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Match ORT profile MatMul events to ONNX graph nodes and classify likely hotspot categories."
    )
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL, help="Exported ONNX model path.")
    parser.add_argument("--sweep-raw", type=Path, default=DEFAULT_SWEEP_RAW, help="ort_sweep_raw_runs.json path.")
    parser.add_argument(
        "--graph-inspection",
        type=Path,
        default=DEFAULT_GRAPH_INSPECTION,
        help="Existing ONNX graph inspection JSON used for metadata in the report.",
    )
    parser.add_argument("--tables-dir", type=Path, default=DEFAULT_TABLES_DIR)
    parser.add_argument("--figures-dir", type=Path, default=DEFAULT_FIGURES_DIR)
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_profile_node_name(name: str) -> str:
    if name.endswith("_kernel_time"):
        return name[: -len("_kernel_time")]
    return name


def load_graph_nodes(model_path: Path) -> list[GraphNode]:
    try:
        import onnx
    except ImportError as exc:
        raise RuntimeError("The onnx Python package is required to match profile nodes to graph nodes.") from exc

    model = onnx.load(str(model_path), load_external_data=False)
    nodes: list[GraphNode] = []
    for index, node in enumerate(model.graph.node):
        nodes.append(
            GraphNode(
                index=index,
                name=node.name,
                op_type=node.op_type,
                inputs=tuple(node.input),
                outputs=tuple(node.output),
            )
        )
    return nodes


def graph_lookup(nodes: list[GraphNode]) -> tuple[dict[str, GraphNode], dict[str, GraphNode]]:
    by_index = {str(node.index): node for node in nodes}
    by_name = {node.name: node for node in nodes if node.name}
    return by_index, by_name


def first_tensor_shape(type_shape: Any) -> list[Any] | None:
    if not isinstance(type_shape, list) or not type_shape:
        return None
    first = type_shape[0]
    if not isinstance(first, dict) or not first:
        return None
    shape = next(iter(first.values()))
    return shape if isinstance(shape, list) else None


def classify_matmul(name: str, input_type_shape: Any = None, output_type_shape: Any = None) -> str:
    lowered = name.lower()
    path = lowered.replace("\\", "/")
    output_shape = first_tensor_shape(output_type_shape)
    output_rank = len(output_shape) if output_shape is not None else None

    if "lm_head" in path:
        return "lm_head"
    if "/mlp/" in path or any(token in path for token in ("/gate_proj/", "/up_proj/", "/down_proj/")):
        return "mlp_projection"
    if any(token in path for token in ("/q_proj/", "/k_proj/", "/v_proj/")):
        return "attention_qkv_projection"
    if "/o_proj/" in path:
        return "attention_output_projection"
    if re.search(r"/self_attn/matmul_1$", path):
        return "attention_v_weighted_sum" if output_rank == 4 else "unknown"
    if re.search(r"/self_attn/matmul(?:_0)?$", path):
        return "attention_qk_score" if output_rank == 4 else "unknown"
    return "unknown"


def shape_to_text(shape: Any) -> str:
    return json.dumps(shape, ensure_ascii=True, separators=(",", ":"))


def profile_path_from_run(run: dict[str, Any], sweep_raw_path: Path) -> Path:
    raw = Path(str(run["profile_json"]))
    if raw.is_file():
        return raw
    candidate = sweep_raw_path.parent / raw.name
    if candidate.is_file():
        return candidate
    return raw


def match_graph_node(event: dict[str, Any], by_index: dict[str, GraphNode], by_name: dict[str, GraphNode]) -> tuple[GraphNode | None, str]:
    args = event.get("args", {})
    profile_name = normalize_profile_node_name(str(event.get("name", "")))
    if profile_name in by_name and by_name[profile_name].op_type == "MatMul":
        return by_name[profile_name], "node_name"

    node_index = str(args.get("node_index", ""))
    if node_index in by_index and by_index[node_index].op_type == "MatMul":
        return by_index[node_index], "node_index_fallback"

    return None, "profile_name_only"


def collect_matmul_events(args: argparse.Namespace, nodes: list[GraphNode]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    sweep = read_json(args.sweep_raw)
    runs = sweep.get("runs", [])
    by_index, by_name = graph_lookup(nodes)

    rows: list[dict[str, Any]] = []
    skipped_profiles: list[str] = []
    for run in runs:
        profile_path = profile_path_from_run(run, args.sweep_raw)
        if not profile_path.is_file():
            skipped_profiles.append(str(profile_path))
            continue

        events = read_json(profile_path)
        phase_node_total_us = 0.0
        for event in events:
            if isinstance(event, dict) and event.get("cat") == "Node":
                phase_node_total_us += float(event.get("dur", 0.0))

        for event in events:
            if not isinstance(event, dict) or event.get("cat") != "Node":
                continue
            event_args = event.get("args", {})
            if event_args.get("op_name") != "MatMul":
                continue

            graph_node, match_method = match_graph_node(event, by_index, by_name)
            profile_name = normalize_profile_node_name(str(event.get("name", "")))
            category_name = graph_node.name if graph_node is not None and match_method == "node_name" else profile_name
            category = classify_matmul(
                category_name,
                input_type_shape=event_args.get("input_type_shape", []),
                output_type_shape=event_args.get("output_type_shape", []),
            )
            rows.append(
                {
                    "phase": run.get("phase"),
                    "context_length": int(run.get("context_length", 0)),
                    "decode_steps": int(run.get("decode_steps", 0)),
                    "run_index": int(run.get("run_index", 0)),
                    "profile_json": str(profile_path),
                    "profile_node_name": profile_name,
                    "graph_node_name": graph_node.name if graph_node is not None else "",
                    "graph_node_index": graph_node.index if graph_node is not None else event_args.get("node_index", ""),
                    "match_method": match_method,
                    "category": category,
                    "duration_us": float(event.get("dur", 0.0)),
                    "phase_node_total_us": phase_node_total_us,
                    "input_type_shape": shape_to_text(event_args.get("input_type_shape", [])),
                    "output_type_shape": shape_to_text(event_args.get("output_type_shape", [])),
                    "provider": event_args.get("provider", ""),
                }
            )

    metadata = {
        "profile_count": len(runs),
        "skipped_profile_count": len(skipped_profiles),
        "skipped_profiles": skipped_profiles,
    }
    return rows, metadata


def aggregate_categories(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], dict[str, Any]] = {}
    matmul_totals: dict[tuple[Any, ...], float] = defaultdict(float)
    phase_profile_totals: dict[tuple[tuple[Any, ...], str, int], float] = {}
    profiles: dict[tuple[Any, ...], set[tuple[str, int]]] = defaultdict(set)
    base_profiles: dict[tuple[Any, ...], set[tuple[str, int]]] = defaultdict(set)

    for row in events:
        base = (row["phase"], row["context_length"], row["decode_steps"])
        key = base + (row["category"],)
        matmul_totals[base] += row["duration_us"]
        phase_profile_totals[(base, row["profile_json"], row["run_index"])] = row["phase_node_total_us"]
        profiles[key].add((row["profile_json"], row["run_index"]))
        base_profiles[base].add((row["profile_json"], row["run_index"]))
        item = groups.setdefault(
            key,
            {
                "phase": row["phase"],
                "context_length": row["context_length"],
                "decode_steps": row["decode_steps"],
                "category": row["category"],
                "profile_count": 0,
                "call_count": 0,
                "total_us": 0.0,
                "matched_node_count": 0,
                "profile_name_only_count": 0,
            },
        )
        item["call_count"] += 1
        item["total_us"] += row["duration_us"]
        if row["match_method"] == "profile_name_only":
            item["profile_name_only_count"] += 1
        else:
            item["matched_node_count"] += 1

    phase_totals: dict[tuple[Any, ...], float] = defaultdict(float)
    for (base, _profile_json, _run_index), total_us in phase_profile_totals.items():
        phase_totals[base] += total_us

    for base, profile_set in base_profiles.items():
        for category in CATEGORIES:
            groups.setdefault(
                base + (category,),
                {
                    "phase": base[0],
                    "context_length": base[1],
                    "decode_steps": base[2],
                    "category": category,
                    "profile_count": len(profile_set),
                    "call_count": 0,
                    "total_us": 0.0,
                    "matched_node_count": 0,
                    "profile_name_only_count": 0,
                },
            )

    output: list[dict[str, Any]] = []
    for key, item in groups.items():
        base = key[:3]
        item["profile_count"] = len(profiles[key]) if profiles[key] else item["profile_count"]
        item["mean_us"] = item["total_us"] / item["call_count"] if item["call_count"] else 0.0
        item["matmul_total_us"] = matmul_totals[base]
        item["matmul_share_pct"] = item["total_us"] / matmul_totals[base] * 100.0 if matmul_totals[base] else 0.0
        item["phase_node_total_us"] = phase_totals[base]
        item["phase_node_share_pct"] = item["total_us"] / phase_totals[base] * 100.0 if phase_totals[base] else 0.0
        output.append(item)

    return sorted(
        output,
        key=lambda item: (item["context_length"], item["decode_steps"], item["phase"], -item["total_us"], item["category"]),
    )


def aggregate_top_nodes(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], dict[str, Any]] = {}
    matmul_totals: dict[tuple[Any, ...], float] = defaultdict(float)

    for row in events:
        base = (row["phase"], row["context_length"], row["decode_steps"])
        matmul_totals[base] += row["duration_us"]
        node_name = row["graph_node_name"] or row["profile_node_name"]
        key = base + (row["category"], node_name)
        item = groups.setdefault(
            key,
            {
                "phase": row["phase"],
                "context_length": row["context_length"],
                "decode_steps": row["decode_steps"],
                "category": row["category"],
                "node_name": node_name,
                "graph_node_name": row["graph_node_name"],
                "profile_node_name": row["profile_node_name"],
                "graph_node_index": row["graph_node_index"],
                "match_method": row["match_method"],
                "provider": row["provider"],
                "call_count": 0,
                "total_us": 0.0,
                "example_input_type_shape": row["input_type_shape"],
                "example_output_type_shape": row["output_type_shape"],
            },
        )
        item["call_count"] += 1
        item["total_us"] += row["duration_us"]

    output: list[dict[str, Any]] = []
    for item in groups.values():
        base = (item["phase"], item["context_length"], item["decode_steps"])
        item["mean_us"] = item["total_us"] / item["call_count"] if item["call_count"] else 0.0
        item["matmul_share_pct"] = item["total_us"] / matmul_totals[base] * 100.0 if matmul_totals[base] else 0.0
        output.append(item)
    return sorted(output, key=lambda item: (item["context_length"], item["decode_steps"], item["phase"], -item["total_us"]))


def phase_summary(category_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], dict[str, Any]] = {}
    totals: dict[str, float] = defaultdict(float)
    for row in category_rows:
        phase = str(row["phase"])
        category = str(row["category"])
        totals[phase] += float(row["total_us"])
        item = groups.setdefault(
            (phase, category),
            {
                "phase": phase,
                "category": category,
                "call_count": 0,
                "total_us": 0.0,
            },
        )
        item["call_count"] += int(row["call_count"])
        item["total_us"] += float(row["total_us"])

    output = []
    for (phase, _category), item in groups.items():
        item["share_pct"] = item["total_us"] / totals[phase] * 100.0 if totals[phase] else 0.0
        output.append(item)
    return sorted(output, key=lambda item: (item["phase"], -item["total_us"], item["category"]))


def global_summary(category_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    total = 0.0
    for row in category_rows:
        category = str(row["category"])
        total += float(row["total_us"])
        item = groups.setdefault(category, {"category": category, "call_count": 0, "total_us": 0.0})
        item["call_count"] += int(row["call_count"])
        item["total_us"] += float(row["total_us"])
    output = []
    for item in groups.values():
        item["share_pct"] = item["total_us"] / total * 100.0 if total else 0.0
        output.append(item)
    return sorted(output, key=lambda item: (-item["total_us"], item["category"]))


def render_category_share_figure(category_rows: list[dict[str, Any]], path: Path) -> None:
    import matplotlib.pyplot as plt

    path.parent.mkdir(parents=True, exist_ok=True)
    groups = sorted(
        {(row["context_length"], row["phase"], row["decode_steps"]) for row in category_rows},
        key=lambda key: (key[0], 0 if key[1] == "prefill" else 1, key[2]),
    )
    labels = [f"P{ctx}" if phase == "prefill" else f"D{ctx}x{steps}" for ctx, phase, steps in groups]
    share_by_group_category = {
        (row["context_length"], row["phase"], row["decode_steps"], row["category"]): float(row["matmul_share_pct"])
        for row in category_rows
    }

    fig_width = max(10.0, len(labels) * 0.55)
    fig, ax = plt.subplots(figsize=(fig_width, 5.6))
    bottom = [0.0] * len(groups)
    for category in CATEGORIES:
        values = [
            share_by_group_category.get((ctx, phase, steps, category), 0.0)
            for ctx, phase, steps in groups
        ]
        ax.bar(labels, values, bottom=bottom, label=category, color=CATEGORY_COLORS[category], linewidth=0)
        bottom = [base + value for base, value in zip(bottom, values)]

    ax.set_ylabel("Share of MatMul time (%)")
    ax.set_xlabel("Profile group: prefill P<context>, decode D<context>x<steps>")
    ax.set_ylim(0, 100)
    ax.set_title("ORT MatMul hotspot categories by context and phase")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=3, frameon=False)
    ax.tick_params(axis="x", labelrotation=45)
    ax.grid(axis="y", color="#DDDDDD", linewidth=0.8)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def format_pct(value: float) -> str:
    return f"{value:.2f}%"


def format_ms_from_us(value: float) -> str:
    return f"{value / 1000.0:.3f}"


def markdown_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]], limit: int | None = None) -> str:
    selected = rows[:limit] if limit is not None else rows
    header = "| " + " | ".join(label for label, _key in columns) + " |"
    sep = "| " + " | ".join("---" for _label, _key in columns) + " |"
    body = []
    for row in selected:
        values = []
        for _label, key in columns:
            value = row.get(key, "")
            if isinstance(value, float):
                if key.endswith("pct"):
                    values.append(format_pct(value))
                elif key.endswith("us"):
                    values.append(format_ms_from_us(value))
                else:
                    values.append(f"{value:.3f}")
            else:
                values.append(str(value))
        body.append("| " + " | ".join(values) + " |")
    return "\n".join([header, sep] + body)


def design_judgement(global_rows: list[dict[str, Any]], unknown_share: float) -> str:
    dominant = global_rows[0]["category"] if global_rows else "unknown"
    qk_share = next((row["share_pct"] for row in global_rows if row["category"] == "attention_qk_score"), 0.0)
    mlp_share = next((row["share_pct"] for row in global_rows if row["category"] == "mlp_projection"), 0.0)
    projection_share = sum(
        row["share_pct"]
        for row in global_rows
        if row["category"]
        in {"attention_qkv_projection", "attention_output_projection", "mlp_projection", "lm_head"}
    )

    lines = []
    if dominant == "mlp_projection" or mlp_share > qk_share:
        lines.append(
            "- 전체 MatMul 시간의 주된 비중은 QK dot-product보다 MLP/linear projection 계열에 더 가깝다. "
            "따라서 FPGA Decode Accelerator의 1차 확장 대상은 QK 단일 블록만이 아니라 decode 단계의 일반 MatVec/MatMul 데이터패스와 weight streaming 구조까지 포함해 검토해야 한다."
        )
    elif qk_share > 0.0:
        lines.append(
            "- QK score MatMul이 관측되지만, 이 결과만으로 전체 MatMul 병목이 QK라고 단정할 수는 없다. "
            "QK primitive는 유지하되 V weighted sum, projection, buffer/stream interface와 함께 설계 우선순위를 비교해야 한다."
        )
    else:
        lines.append(
            "- 현재 분류에서는 QK score MatMul을 확정할 수 없으므로 QK 전용 가속기를 전체 decode 병목의 대표로 놓기 어렵다."
        )

    lines.append(
        f"- attention/MLP/lm_head projection으로 분류된 일반 MatVec/MatMul 계열 합계는 전체 MatMul 시간의 {projection_share:.2f}%이다."
    )
    if unknown_share > 0.0:
        lines.append(
            f"- unknown 비중이 {unknown_share:.2f}% 남아 있으므로, 이 부분은 노드명과 graph path만으로는 설계 대상 연산을 확정하지 않는다."
        )
    return "\n".join(lines)


def write_report(
    args: argparse.Namespace,
    category_rows: list[dict[str, Any]],
    top_rows: list[dict[str, Any]],
    metadata: dict[str, Any],
    graph_metadata: dict[str, Any],
) -> None:
    global_rows = global_summary(category_rows)
    phase_rows = phase_summary(category_rows)
    unknown_share = next((row["share_pct"] for row in global_rows if row["category"] == "unknown"), 0.0)
    qk_share = next((row["share_pct"] for row in global_rows if row["category"] == "attention_qk_score"), 0.0)

    report = f"""# ORT MatMul Hotspot Category Analysis

## 입력과 방법

- ONNX model: `{args.model}`
- ORT sweep raw runs: `{args.sweep_raw}`
- ONNX graph inspection: `{args.graph_inspection}`
- 분석 profile 수: {metadata["profile_count"] - metadata["skipped_profile_count"]} / {metadata["profile_count"]}
- ONNX graph node 수: {graph_metadata.get("total_node_count", "unknown")}
- ONNX MatMul node 수: {graph_metadata.get("operator_histogram", {}).get("MatMul", "unknown")}

ORT profile JSON의 `Node` event 중 `op_name == "MatMul"`인 항목을 읽고, profile event의 normalized node name을 우선 ONNX graph node name에 매칭했다. `node_index`는 ORT 최적화 이후 원본 ONNX graph index와 어긋날 수 있으므로 graph metadata 보조 fallback으로만 사용하고, category 분류에는 profile/graph node name path를 사용했다. 분류는 node name/path가 명확한 경우에만 적용했다.

분류 규칙은 다음과 같다.

- `q_proj`, `k_proj`, `v_proj`: `attention_qkv_projection`
- attention 내부 bare `MatMul`이고 profile output이 attention score 형태의 4D tensor인 경우: `attention_qk_score`
- attention 내부 `MatMul_1`이고 profile output이 4D tensor인 경우: `attention_v_weighted_sum`
- `o_proj`: `attention_output_projection`
- `mlp/*_proj`: `mlp_projection`
- `lm_head`: `lm_head`
- 위 규칙으로 확정할 수 없는 MatMul: `unknown`

## MatMul Category 비중

아래 비중은 전체 MatMul 시간 중 category별 비중이다. 단위 `total_us` 열은 표에서는 ms로 표시한다.

{markdown_table(global_rows, [("category", "category"), ("call_count", "call_count"), ("total_ms", "total_us"), ("share", "share_pct")])}

## Prefill/Decode 차이

phase별 MatMul category 비중은 다음과 같다.

{markdown_table(phase_rows, [("phase", "phase"), ("category", "category"), ("call_count", "call_count"), ("total_ms", "total_us"), ("share", "share_pct")])}

세부 context/decode-step별 값은 `paper_assets/tables/ort_matmul_category_by_context.csv`에 저장했다. `paper_assets/figures/ort_matmul_category_share.png`는 같은 값을 stacked share로 시각화한다.

## Top MatMul Nodes

아래 표는 context/phase/decode-step을 모두 합쳐 시간이 큰 MatMul node 상위 20개다. 단위 `total_us` 열은 표에서는 ms로 표시한다.

{markdown_table(sorted(top_rows, key=lambda row: -float(row["total_us"])), [("category", "category"), ("phase", "phase"), ("ctx", "context_length"), ("steps", "decode_steps"), ("node", "node_name"), ("calls", "call_count"), ("total_ms", "total_us"), ("matmul_share", "matmul_share_pct")], limit=20)}

## QK Dot-Product 확인 가능 여부

- `attention_qk_score`로 분류된 MatMul 비중: {qk_share:.2f}%
- 이 값은 node name/path가 attention 내부 bare `MatMul`로 남아 있고 profile output이 4D attention score 형태로 확인되는 항목에 한정한 보수적 분류다.
- `MatMul`이 곧 QK라고 가정하지 않았으며, `rotary_emb/MatMul`처럼 이름/path가 QK score를 확정하지 못하는 항목은 `unknown`으로 남겼다.
- unknown 비중: {unknown_share:.2f}%

## FPGA Decode Accelerator 설계 판단

{design_judgement(global_rows, unknown_share)}

현 시점의 하드웨어 해석은 기존 DE10-Lite INT8 QK dot-product primitive의 타당성을 넘어서지 않는다. 이 분석은 다음 설계 단계에서 QK score, V weighted sum, attention/MLP projection, 그리고 stream/buffer interface 중 무엇을 우선 검토할지 정하기 위한 host-side ORT 근거로만 사용한다.

## 한계

- 분류는 node name/path 기반이다. node name이 불충분하거나 graph 최적화로 의미가 사라진 경우 category를 확정하지 않는다.
- ORT CPUExecutionProvider profile의 시간은 host-side 실행 특성을 반영한다. FPGA primitive의 cycle 또는 end-to-end speedup으로 직접 환산하지 않는다.
- MatMul 내부 shape와 인접 연산은 보조 정보로 CSV에 남겼지만, 이름/path가 불충분한 경우 억지로 category를 추정하지 않았다.
"""
    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    args.report_path.write_text(report, encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.tables_dir.mkdir(parents=True, exist_ok=True)
    args.figures_dir.mkdir(parents=True, exist_ok=True)

    graph_metadata = read_json(args.graph_inspection) if args.graph_inspection.is_file() else {}
    nodes = load_graph_nodes(args.model)
    events, metadata = collect_matmul_events(args, nodes)
    category_rows = aggregate_categories(events)
    top_rows = aggregate_top_nodes(events)

    category_path = args.tables_dir / "ort_matmul_category_by_context.csv"
    top_nodes_path = args.tables_dir / "ort_matmul_top_nodes.csv"
    figure_path = args.figures_dir / "ort_matmul_category_share.png"

    write_csv(
        category_path,
        [
            "phase",
            "context_length",
            "decode_steps",
            "category",
            "profile_count",
            "call_count",
            "total_us",
            "mean_us",
            "matmul_total_us",
            "matmul_share_pct",
            "phase_node_total_us",
            "phase_node_share_pct",
            "matched_node_count",
            "profile_name_only_count",
        ],
        category_rows,
    )
    write_csv(
        top_nodes_path,
        [
            "phase",
            "context_length",
            "decode_steps",
            "category",
            "node_name",
            "graph_node_name",
            "profile_node_name",
            "graph_node_index",
            "match_method",
            "provider",
            "call_count",
            "total_us",
            "mean_us",
            "matmul_share_pct",
            "example_input_type_shape",
            "example_output_type_shape",
        ],
        top_rows,
    )
    render_category_share_figure(category_rows, figure_path)
    write_report(args, category_rows, top_rows, metadata, graph_metadata)

    print(f"Wrote {category_path}")
    print(f"Wrote {top_nodes_path}")
    print(f"Wrote {figure_path}")
    print(f"Wrote {args.report_path}")


if __name__ == "__main__":
    main()
