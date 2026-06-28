#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


SUPPORTED_DIMS = [16, 32, 64, 128]
DEVICE_NAME = "10M50DAF484C7G"
FAMILY_NAME = "MAX 10"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create and compile Quartus synthesis-only projects for the INT8 QK dot-product dim sweep."
    )
    parser.add_argument("--quartus-sh", required=True, help="Resolved path to quartus_sh")
    parser.add_argument("--repo-root", required=True, help="Repository root")
    parser.add_argument("--dims", nargs="+", type=int, default=SUPPORTED_DIMS, help="Dims to compile")
    return parser.parse_args()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_qpf(project_name: str) -> str:
    return f"PROJECT_REVISION = {project_name}\n"


def make_qsf(project_name: str, top_level: str, wrapper_verilog: Path, core_verilog: Path, sdc_file: Path) -> str:
    return "\n".join(
        [
            f'set_global_assignment -name FAMILY "{FAMILY_NAME}"',
            f"set_global_assignment -name DEVICE {DEVICE_NAME}",
            f"set_global_assignment -name TOP_LEVEL_ENTITY {top_level}",
            "set_global_assignment -name PROJECT_OUTPUT_DIRECTORY output_files",
            f'set_global_assignment -name VERILOG_FILE "{wrapper_verilog}"',
            f'set_global_assignment -name VERILOG_FILE "{core_verilog}"',
            f'set_global_assignment -name SDC_FILE "{sdc_file}"',
            "",
        ]
    )


def make_sdc() -> str:
    return "\n".join(
        [
            "create_clock -name CLOCK_50 -period 20.000 [get_ports {CLOCK_50}]",
            "derive_clock_uncertainty",
            "",
        ]
    )


def ensure_verilog_files(repo_root: Path, dim: int) -> tuple[Path, Path]:
    generated_dir = repo_root / "quartus" / "dim_sweep" / "generated_verilog"
    core_verilog = generated_dir / f"DotProductInt8_dim{dim}.v"
    wrapper_verilog = generated_dir / f"DotProductInt8SweepTop_dim{dim}.v"
    missing = [str(path) for path in (core_verilog, wrapper_verilog) if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "Missing generated Verilog for dim sweep. Run 'nix develop -c just spinal-generate-sweep' first.\n"
            f"missing files: {', '.join(missing)}"
        )
    return core_verilog.resolve(), wrapper_verilog.resolve()


def run_compile(quartus_sh: Path, project_dir: Path, project_name: str) -> None:
    log_path = project_dir / "quartus_compile.log"
    command = [str(quartus_sh), "--flow", "compile", project_name]
    with log_path.open("w", encoding="utf-8") as handle:
        result = subprocess.run(command, cwd=project_dir, stdout=handle, stderr=subprocess.STDOUT, text=True)
    if result.returncode != 0:
        log_tail = log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-40:]
        raise RuntimeError(
            f"Quartus compile failed for {project_name}. See {log_path}.\n"
            + "\n".join(log_tail)
        )


def compile_dim(quartus_sh: Path, repo_root: Path, dim: int) -> dict[str, str]:
    core_verilog, wrapper_verilog = ensure_verilog_files(repo_root, dim)
    sweep_root = repo_root / "quartus" / "dim_sweep"
    project_dir = sweep_root / "projects" / f"dim{dim}"
    project_name = f"dot_product_dim{dim}"
    top_level = f"DotProductInt8SweepTop_dim{dim}"
    qpf_path = project_dir / f"{project_name}.qpf"
    qsf_path = project_dir / f"{project_name}.qsf"
    sdc_path = project_dir / f"{project_name}.sdc"

    write_text(qpf_path, make_qpf(project_name))
    write_text(sdc_path, make_sdc())
    write_text(qsf_path, make_qsf(project_name, top_level, wrapper_verilog, core_verilog, sdc_path.resolve()))

    run_compile(quartus_sh, project_dir, project_name)
    output_dir = project_dir / "output_files"

    return {
        "dim": str(dim),
        "project_dir": str(project_dir.resolve()),
        "project_name": project_name,
        "top_level": top_level,
        "core_verilog": str(core_verilog),
        "wrapper_verilog": str(wrapper_verilog),
        "output_dir": str(output_dir.resolve()),
    }


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    quartus_sh = Path(args.quartus_sh).resolve()

    if not quartus_sh.is_file():
        print(f"error: quartus_sh not found: {quartus_sh}", file=sys.stderr)
        return 1

    unsupported = [dim for dim in args.dims if dim not in SUPPORTED_DIMS]
    if unsupported:
        print(
            f"error: unsupported dims requested: {unsupported}. Supported dims: {SUPPORTED_DIMS}",
            file=sys.stderr,
        )
        return 2

    manifest = []
    for dim in args.dims:
        print(f"[quartus-dim-sweep] compiling dim={dim}")
        result = compile_dim(quartus_sh, repo_root, dim)
        manifest.append(result)
        print(json.dumps(result, indent=2))

    manifest_path = repo_root / "quartus" / "dim_sweep" / "projects" / "manifest.json"
    write_text(manifest_path, json.dumps(manifest, indent=2) + "\n")
    print(f"Wrote {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
