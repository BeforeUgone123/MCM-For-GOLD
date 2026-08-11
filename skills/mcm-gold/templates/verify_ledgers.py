#!/usr/bin/env python3
"""按 workspace-templates.md 的契约核对工作区里的 CSV 台账。

**契约从文档读，不在这里再抄一份。**`workspace-templates.md` 已经逐个台账给出了表头
和样例行；把表头复制进检查器就会产生第二份真相，两边迟早各说各话。这里直接解析那份
文档，文档改了检查自动跟上。

要解决的失效模式，与 SOURCE_DATA_MAP 那次同源：台账被多个阶段的 SKILL.md 反复要求，
却没有任何机检，于是「有没有建」「建了有没有填」全靠自觉。逐一扫描 76 个被要求的产物
后，44 个零机检，其中 NATURE_QA.csv 被 6 个阶段引用、T8 Gate 明写「无未解释
DRAFT/BLOCKED」，而实际工作区里根本没有这个文件。

检查的都是可证伪的事实：
  - 表头是否与契约一致（少列会让下游读到 None，多列往往是手工改表的痕迹）；
  - 是否只有表头没有数据行；
  - 数据行里是否残留 `<实际观察>` 这类模板占位符——从模板复制时连样例行一起带进来、
    忘了删，是最常见的一种「看着填了其实没填」；
  - `*_at` 时间戳是否是合法 ISO8601。AGENTS.md 规定时间戳必须由 `date -Iseconds`
    之类的命令取、不得手写，而手写留下的痕迹通常就是格式不合法或与文件 mtime 矛盾。

用法：
    python3 verify_ledgers.py --workspace MCM-Result
    python3 verify_ledgers.py --workspace MCM-Result \\
        --require NATURE_QA.csv --require CLAIM_LEDGER.csv \\
        --out MCM-Result/Review-Results/T8_LEDGERS.json
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import re
import sys
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parent / "workspace-templates.md"

# 台账可能落在这两个目录之一，取决于它是过程记录还是 review 结果
SEARCH_DIRS = ("Intermediate-Outputs", "Review-Results")

SECTION_RE = re.compile(r"^##\s+([A-Za-z0-9_]+\.csv)\s*$", re.M)
FENCE_RE = re.compile(r"```csv\n(.*?)\n```", re.S)
PLACEHOLDER_RE = re.compile(r"<[^<>\n]{1,40}>")
TIMESTAMP_COLUMN_RE = re.compile(r"(_at|_time|timestamp)$", re.I)


def parse_contracts(path: Path) -> dict[str, list[str]]:
    """从 workspace-templates.md 提取 {台账文件名: 表头列表}。"""
    text = path.read_text(encoding="utf-8")
    contracts: dict[str, list[str]] = {}
    matches = list(SECTION_RE.finditer(text))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        fence = FENCE_RE.search(text, match.end(), end)
        if not fence:
            continue
        first_line = fence.group(1).splitlines()[0]
        contracts[match.group(1)] = [c.strip() for c in first_line.split(",")]
    return contracts


def locate(workspace: Path, name: str) -> Path | None:
    for folder in SEARCH_DIRS:
        candidate = workspace / folder / name
        if candidate.is_file():
            return candidate
    return None


def valid_timestamp(value: str) -> bool:
    value = value.strip()
    if not value:
        return False
    try:
        _dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def check_one(name: str, header: list[str], path: Path) -> tuple[list[str], list[str], int]:
    errors: list[str] = []
    warnings: list[str] = []

    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    if not rows:
        return [f"LEDGER_EMPTY {name} 是空文件"], warnings, 0

    actual = [c.strip() for c in rows[0]]
    if actual != header:
        missing = [c for c in header if c not in actual]
        extra = [c for c in actual if c not in header]
        errors.append(
            f"LEDGER_HEADER_DRIFT {name} 表头与 workspace-templates.md 不符"
            + (f"，缺列 {missing}" if missing else "")
            + (f"，多列 {extra}" if extra else ""))

    data = [r for r in rows[1:] if any((c or "").strip() for c in r)]
    if not data:
        errors.append(f"LEDGER_EMPTY {name} 只有表头、零条目")
        return errors, warnings, 0

    index = {c: i for i, c in enumerate(actual)}
    for line_number, row in enumerate(data, start=2):
        joined = ",".join(row)
        stub = PLACEHOLDER_RE.findall(joined)
        if stub:
            errors.append(
                f"LEDGER_PLACEHOLDER_ROW {name}:{line_number} 残留模板占位符 "
                f"{stub[:3]}——多半是复制样例行后没删或没填")
        for column, position in index.items():
            if not TIMESTAMP_COLUMN_RE.search(column) or position >= len(row):
                continue
            value = row[position]
            if value.strip() and not valid_timestamp(value):
                warnings.append(
                    f"LEDGER_TIMESTAMP_INVALID {name}:{line_number} {column}="
                    f"{value.strip()!r} 不是合法 ISO8601（时间戳应由 date -Iseconds 取）")
    return errors, warnings, len(data)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--require", action="append", default=[],
                        help="本阶段必须存在的台账；缺失从 warning 升为 error。可重复")
    parser.add_argument("--templates", type=Path, default=TEMPLATES)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    contracts = parse_contracts(args.templates)
    if not contracts:
        print(f"FAIL_CONTRACT 没能从 {args.templates} 解析出任何台账契约")
        return 2

    required = set(args.require)
    unknown = required - set(contracts)
    if unknown:
        print(f"FAIL_CONTRACT --require 指定了契约里没有的台账：{sorted(unknown)}")
        return 2

    errors: list[str] = []
    warnings: list[str] = []
    seen: dict[str, dict] = {}

    for name, header in sorted(contracts.items()):
        path = locate(workspace, name)
        if path is None:
            line = (f"LEDGER_MISSING {name} 不存在"
                    f"（找过 {'、'.join(SEARCH_DIRS)}）")
            (errors if name in required else warnings).append(line)
            seen[name] = {"present": False}
            continue
        file_errors, file_warnings, count = check_one(name, header, path)
        errors.extend(file_errors)
        warnings.extend(file_warnings)
        seen[name] = {"present": True, "rows": count,
                      "path": path.relative_to(workspace).as_posix()}

    status = "FAIL_CONTRACT" if errors else ("NEEDS_HUMAN" if warnings else "PASS")
    report = {"status": status, "contracts": len(contracts),
              "ledgers": seen, "errors": errors, "warnings": warnings}

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                            encoding="utf-8")

    present = sum(1 for v in seen.values() if v.get("present"))
    print(f"契约 {len(contracts)} 个台账，工作区里存在 {present} 个：{status}")
    for line in errors:
        print(f"  [error]   {line}")
    for line in warnings:
        print(f"  [warning] {line}")
    if args.out:
        print(f"报告：{args.out}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
