#!/usr/bin/env python3
"""扫描工作区，生成 SOURCE_DATA_MAP.csv 的骨架。

`verify_evidence_map.py` 把「登记的哈希与文件对不上」变成了可检出的错误，但四个演练
工作区里三个**根本没有这个文件**、第四个只有表头。加机检只能让缺失暴露，不能让它被
填上——一条从未被执行的要求，症结往往不是不自觉，而是执行成本：手工维护一张 13 列
× 十几行、每行还要现算 SHA-256 的表，谁都会往后拖，拖到 T8 就来不及了。

所以这里把能由机器确定的列直接填实：

    dataset_id / kind / actual_location / sha256 / access_route / generated_by /
    status / updated_at

留给人的只剩语义列——`claim_ids`、`result_ids`、`source_ids`、`restriction`、
`license_or_terms`。它们留空而不是填 `<占位符>`：占位符会被 `verify_ledgers.py` 判为
`LEDGER_PLACEHOLDER_ROW`，而空值老老实实表示「还没填」。status 一律 `PENDING`，
要改成 `VERIFIED` 得由人逐行确认。

**这个脚本不发明事实**：路径是扫出来的，哈希是现算的，生成脚本靠「图源表与绘图脚本
同在一个工作区」这种可验证的关系推断，推断不出就留空。

用法：
    python3 seed_evidence_map.py --workspace MCM-Result            # 预览
    python3 seed_evidence_map.py --workspace MCM-Result --write    # 落盘
    python3 seed_evidence_map.py --workspace MCM-Result --write --merge  # 保留已填行
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import sys
from pathlib import Path

COLUMNS = [
    "dataset_id", "kind", "claim_ids", "result_ids", "source_ids",
    "actual_location", "sha256", "access_route", "restriction",
    "license_or_terms", "generated_by", "status", "updated_at",
]

FIGURE_SOURCE_SUFFIXES = {".csv", ".tsv"}
MODEL_OUTPUT_SUFFIXES = {".xlsx", ".xls", ".csv", ".json", ".npz", ".parquet"}
DATA_SUFFIXES = {".xlsx", ".xls", ".csv", ".tsv", ".json", ".txt", ".dat",
                 ".npz", ".parquet", ".mat"}

SKIP_NAMES = {"MANIFEST.sha256", "RESULTS.jsonl", "RESULTS.md",
              "SOURCE_DATA_MAP.csv", "TOPIC_TERMS.txt"}
CACHE_DIRS = {".venv", "venv", "__pycache__", "node_modules", ".git", "tmp",
              "logs", "reproduction", "pycache", "humanize"}


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def walk(base: Path):
    if not base.is_dir():
        return
    stack = [base]
    while stack:
        current = stack.pop()
        try:
            children = sorted(current.iterdir())
        except OSError:
            continue
        for child in children:
            if child.is_dir():
                if child.name not in CACHE_DIRS and not child.name.startswith("."):
                    stack.append(child)
            elif not child.name.startswith(".") and child.name not in SKIP_NAMES:
                yield child


def guess_generator(workspace: Path, target: Path) -> str:
    """只在关系可验证时才写生成脚本，猜不出就留空。

    图源表与图同名（F-001-x.csv / F-001-x.pdf）是本套契约里明确的约定，绘图脚本
    因此可以按「Data-Scripts 下引用了该文件名的脚本」定位。定位不到就不写——
    写一个猜的脚本名比留空更糟，它会让人以为这条已经核实过。
    """
    scripts = workspace / "Data-Scripts"
    if not scripts.is_dir():
        return ""
    needle = target.name
    for script in sorted(scripts.rglob("*.py")):
        try:
            if needle in script.read_text(encoding="utf-8", errors="ignore"):
                return script.relative_to(workspace).as_posix()
        except OSError:
            continue
    return ""


def collect(workspace: Path) -> list[dict[str, str]]:
    stamp = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
    rows: list[dict[str, str]] = []

    def add(path: Path, kind: str, route: str) -> None:
        rows.append({
            "dataset_id": "", "kind": kind, "claim_ids": "", "result_ids": "",
            "source_ids": "",
            "actual_location": path.relative_to(workspace).as_posix(),
            "sha256": sha256_of(path), "access_route": route,
            "restriction": "", "license_or_terms": "",
            "generated_by": guess_generator(workspace, path),
            "status": "PENDING", "updated_at": stamp,
        })

    for path in walk(workspace / "Competition-Materials"):
        if path.suffix.lower() in DATA_SUFFIXES:
            add(path, "raw", "official_attachment")

    for path in walk(workspace / "Data-Figures"):
        if path.suffix.lower() in FIGURE_SOURCE_SUFFIXES:
            add(path, "figure_source", "support_package")

    for folder, kind in ((workspace / "Paper-Outputs" / "results", "model_output"),
                         (workspace / "Intermediate-Outputs" / "processed", "processed")):
        for path in walk(folder):
            if path.suffix.lower() in MODEL_OUTPUT_SUFFIXES:
                add(path, kind, "support_package")

    prefix = {"raw": "DS-R", "figure_source": "DS-F",
              "model_output": "DS-M", "processed": "DS-P"}
    counters: dict[str, int] = {}
    for row in rows:
        key = row["kind"]
        counters[key] = counters.get(key, 0) + 1
        row["dataset_id"] = f"{prefix.get(key, 'DS')}-{counters[key]:03d}"
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--write", action="store_true", help="落盘，否则只预览")
    parser.add_argument("--merge", action="store_true",
                        help="保留已有文件里 actual_location 相同的行，只补新条目")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    if not workspace.is_dir():
        print(f"WORKSPACE_NOT_FOUND {workspace}")
        return 2

    rows = collect(workspace)
    if not rows:
        print("没扫到可登记的数据文件（官方附件、图源表、结果文件、处理数据均为空）")
        return 1

    target = workspace / "Intermediate-Outputs" / "SOURCE_DATA_MAP.csv"
    kept: list[dict[str, str]] = []
    if args.merge and target.is_file():
        with target.open(encoding="utf-8", newline="") as handle:
            kept = [r for r in csv.DictReader(handle)
                    if (r.get("actual_location") or "").strip()]
        known = {r["actual_location"] for r in kept}
        rows = [r for r in rows if r["actual_location"] not in known]
        print(f"合并模式：保留已有 {len(kept)} 行，新增 {len(rows)} 行")

    for row in rows:
        print(f"  {row['dataset_id']:<10} {row['kind']:<14} "
              f"{row['actual_location']}")

    if not args.write:
        print(f"\n共 {len(rows)} 条。加 --write 落盘到 "
              f"{target.relative_to(workspace)}")
        return 0

    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        for row in kept + rows:
            writer.writerow({c: row.get(c, "") for c in COLUMNS})

    print(f"\n已写入 {target}（{len(kept) + len(rows)} 行）")
    print("语义列（claim_ids/result_ids/source_ids/restriction/license_or_terms）留空待补，"
          "status 一律 PENDING——改成 VERIFIED 必须逐行人工确认。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
