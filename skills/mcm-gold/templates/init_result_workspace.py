#!/usr/bin/env python3
"""Create the canonical MCM-Result workspace without touching existing files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DIRECTORIES = (
    "Reference-Papers",
    "Data-Scripts",
    "Competition-Materials",
    "Paper-Outputs",
    "Data-Figures",
    "Intermediate-Outputs",
    "Review-Results",
)


def initialize(workdir: Path) -> dict[str, object]:
    result_root = (workdir.resolve() / "MCM-Result")
    result_root.mkdir(parents=True, exist_ok=True)

    created: list[str] = []
    existing: list[str] = []
    for name in DIRECTORIES:
        path = result_root / name
        if path.exists() and not path.is_dir():
            raise SystemExit(f"目标路径存在但不是目录: {path}")
        if path.is_dir():
            existing.append(name)
        else:
            path.mkdir()
            created.append(name)

    return {
        "result_root": str(result_root),
        "directories": list(DIRECTORIES),
        "created": created,
        "existing": existing,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="初始化 MCM-Result 标准输出目录")
    parser.add_argument(
        "--workdir",
        type=Path,
        default=Path.cwd(),
        help="工作目录，默认当前目录",
    )
    args = parser.parse_args()
    print(json.dumps(initialize(args.workdir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
