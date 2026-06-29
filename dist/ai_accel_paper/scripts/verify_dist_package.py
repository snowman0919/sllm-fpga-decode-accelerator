#!/usr/bin/env python3
"""Verify dist package manifest checksums."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-dir", default="dist/ai_accel_paper")
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    args = parse_args()
    base = Path(args.package_dir)
    manifest_path = base / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    bad: list[str] = []
    for item in manifest.get("files", []):
        rel = item["path"]
        path = base / rel
        if not path.exists():
            bad.append(f"{rel}: missing")
            continue
        observed = sha256(path)
        expected = item["sha256"]
        if observed != expected:
            bad.append(f"{rel}: observed {observed} expected {expected}")
    if bad:
        raise SystemExit("dist package checksum verification failed:\n" + "\n".join(bad))
    print(f"verified {len(manifest.get('files', []))} files in {base}")


if __name__ == "__main__":
    main()
