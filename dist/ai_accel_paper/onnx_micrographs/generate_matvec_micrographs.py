#!/usr/bin/env python3
"""Generate small ONNX MatVec/MatMul micrographs used by the harnesses."""

from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default="onnx_micrographs")
    parser.add_argument("--input-dim", type=int, default=16)
    parser.add_argument("--output-dim", type=int, default=4)
    parser.add_argument("--name", default="matvec_cpu_baseline.onnx")
    return parser.parse_args()


def make_graph(path: Path, input_dim: int, output_dim: int, name: str) -> None:
    import onnx
    from onnx import TensorProto, helper

    activation = helper.make_tensor_value_info("activation", TensorProto.FLOAT, [1, input_dim])
    weight = helper.make_tensor_value_info("weight", TensorProto.FLOAT, [input_dim, output_dim])
    output = helper.make_tensor_value_info("output", TensorProto.FLOAT, [1, output_dim])
    node = helper.make_node("MatMul", ["activation", "weight"], ["output"], name="MatVecMatMul")
    graph = helper.make_graph([node], "fixed_matvec_micrograph", [activation, weight], [output])
    model = helper.make_model(
        graph,
        producer_name="sllm-fpga-decode-accelerator",
        opset_imports=[helper.make_operatorsetid("", 17)],
    )
    model.ir_version = min(model.ir_version, 10)
    onnx.checker.check_model(model)
    path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, path)


def make_matmulinteger_graph(path: Path, input_dim: int, output_dim: int, name: str) -> None:
    import onnx
    from onnx import TensorProto, helper

    activation = helper.make_tensor_value_info("activation", TensorProto.INT8, [1, input_dim])
    weight = helper.make_tensor_value_info("weight", TensorProto.INT8, [input_dim, output_dim])
    output = helper.make_tensor_value_info("output", TensorProto.INT32, [1, output_dim])
    node = helper.make_node("MatMulInteger", ["activation", "weight"], ["output"], name="MatVecMatMulInteger")
    graph = helper.make_graph([node], "fixed_matvec_integer_micrograph", [activation, weight], [output])
    model = helper.make_model(
        graph,
        producer_name="sllm-fpga-decode-accelerator",
        opset_imports=[helper.make_operatorsetid("", 17)],
    )
    model.ir_version = min(model.ir_version, 10)
    onnx.checker.check_model(model)
    path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, path)


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    make_graph(out_dir / args.name, args.input_dim, args.output_dim, args.name)
    make_graph(out_dir / "matvec_fpga_custom_stub.onnx", args.input_dim, args.output_dim, "matvec_fpga_custom_stub.onnx")
    make_matmulinteger_graph(
        out_dir / "matvec_int8_matmulinteger.onnx",
        args.input_dim,
        args.output_dim,
        "matvec_int8_matmulinteger.onnx",
    )
    print(f"wrote {out_dir / args.name}")
    print(f"wrote {out_dir / 'matvec_fpga_custom_stub.onnx'}")
    print(f"wrote {out_dir / 'matvec_int8_matmulinteger.onnx'}")


if __name__ == "__main__":
    main()
