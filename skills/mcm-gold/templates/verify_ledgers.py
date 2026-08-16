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
  - 台账是否落在契约声明的归属目录，别的目录里有没有同名副本（`LEDGER_STRAY_COPY`）。
    两份并存时只有一份被机检读到，对另一份的更新永久失效，而报告照样全绿；
  - 表头是否与契约一致（少列会让下游读到 None，多列往往是手工改表的痕迹）；
  - 是否只有表头没有数据行；
  - 数据行里是否残留 `<实际观察>` 这类模板占位符——从模板复制时连样例行一起带进来、
    忘了删，是最常见的一种「看着填了其实没填」；
  - `*_at` 时间戳是否是合法 ISO8601。AGENTS.md 规定时间戳必须由 `date -Iseconds`
    之类的命令取、不得手写，而手写留下的痕迹通常就是格式不合法或与文件 mtime 矛盾；
  - 路径型列（`file_location`/`file`/`script`/`artifact`/`source_table`/`generated_by`/
    `*_location`）指向的文件是否真的存在。这些列名分布在 5 个台账里、语义一致，所以
    规则写一次即可。**「已核验」却指向不存在的文件，是通过项最容易空转的形态**：
    读的人无从复核，而报告照样全绿；
  - id 列是否为空、`observed` 是否为空。没有实际观测值的「通过项」不构成证据。

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

# 台账落在这两个目录之一，取决于它是过程记录还是 review 结果。
# 具体哪一个由 workspace-templates.md 各小节的「归属目录」行声明，本文件不再自己判断——
# 早先这里是「两个目录先到先得」，而文档对 FIGURE_EVIDENCE/NATURE_QA 的归属自相矛盾，
# 于是不同会话在两处各建一份，检查器只读到先命中的那份，另一份的更新被静默忽略。
SEARCH_DIRS = ("Intermediate-Outputs", "Review-Results")

SECTION_RE = re.compile(r"^##\s+([A-Za-z0-9_]+\.csv)\s*$", re.M)
FENCE_RE = re.compile(r"```csv\n(.*?)\n```", re.S)
# 归属目录：`MCM-Result/Review-Results/`
HOME_DIR_RE = re.compile(r"^归属目录：`(?:MCM-Result/)?([A-Za-z-]+)/?`", re.M)
# `<` 后紧跟数字或 `=` 的是数学比较，不是模板占位符。实测误报：某台账写
# 「正文汉字 10674<15000、摘要 879>850」，`<15000、摘要 879>` 被整段当成了占位符。
PLACEHOLDER_RE = re.compile(r"<(?![\d=])[^<>\n]{1,40}>")
TIMESTAMP_COLUMN_RE = re.compile(r"(_at|_time|timestamp)$", re.I)

# 跨表通用的列型。列名相同的列在不同台账里语义一致，所以规则写一次即可：
# file_location / file / script / artifact / source_table / generated_by /
# actual_location 分布在 5 个台账里，全部应当指向真实存在的文件。
PATH_COLUMN_RE = re.compile(
    r"^(file|artifact|script|source_table|generated_by|.*_location|.*_path|path)$",
    re.I)
# 只有长得像相对/绝对路径的值才去查存在性；`P-001`、`见正文` 这类不算
PATHLIKE_RE = re.compile(r"^[\w./~-]+/[\w./-]+\.\w{1,8}$")
STATUS_COLUMN_RE = re.compile(r"^(status|human_status|human_gate)$", re.I)
OBSERVED_COLUMN_RE = re.compile(r"^observed$", re.I)


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


def parse_home_dirs(path: Path) -> dict[str, str]:
    """从 workspace-templates.md 提取 {台账文件名: 归属目录}。

    与表头同源：契约文档改了归属，检查自动跟上；这里不留第二份判断。
    """
    text = path.read_text(encoding="utf-8")
    homes: dict[str, str] = {}
    matches = list(SECTION_RE.finditer(text))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        declared = HOME_DIR_RE.search(text, match.end(), end)
        if declared and declared.group(1) in SEARCH_DIRS:
            homes[match.group(1)] = declared.group(1)
    return homes


def locate(workspace: Path, name: str,
           home: str | None) -> tuple[Path | None, list[Path]]:
    """返回 (采用的文件, 主目录之外的同名副本)。

    契约声明了归属目录时**只认那一个目录**，别处的同名文件作为 stray 单独报出——
    两份台账并存时，静默采用其中一份等于让另一份的更新永久失效。
    """
    hits = [workspace / folder / name for folder in SEARCH_DIRS]
    hits = [path for path in hits if path.is_file()]
    if not hits:
        return None, []
    if home is None:
        return hits[0], hits[1:]
    primary = workspace / home / name
    chosen = primary if primary.is_file() else hits[0]
    strays = [path for path in hits if path != chosen]
    return chosen, strays


def valid_timestamp(value: str) -> bool:
    value = value.strip()
    if not value:
        return False
    try:
        _dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def resolve_in_workspace(workspace: Path, raw: str) -> Path:
    """台账里的路径可能带工作区前缀，也可能不带；两种都认。"""
    candidate = Path(raw.strip().replace("\\", "/"))
    if candidate.is_absolute():
        return candidate
    for base in (workspace, workspace.parent):
        resolved = base / candidate
        if resolved.exists():
            return resolved
    return workspace / candidate


def check_one(name: str, header: list[str], path: Path,
              workspace: Path) -> tuple[list[str], list[str], int]:
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
    id_column = actual[0] if actual else ""
    for line_number, row in enumerate(data, start=2):
        joined = ",".join(row)
        stub = PLACEHOLDER_RE.findall(joined)
        if stub:
            errors.append(
                f"LEDGER_PLACEHOLDER_ROW {name}:{line_number} 残留模板占位符 "
                f"{stub[:3]}——多半是复制样例行后没删或没填")
        for column, position in index.items():
            value = row[position].strip() if position < len(row) else ""

            if TIMESTAMP_COLUMN_RE.search(column) and value and not valid_timestamp(value):
                warnings.append(
                    f"LEDGER_TIMESTAMP_INVALID {name}:{line_number} {column}="
                    f"{value!r} 不是合法 ISO8601（时间戳应由 date -Iseconds 取）")

            # 台账登记的路径必须真的存在。这是「通过项」最容易空转的地方：
            # 写一条「已核验」却指向一个不存在的文件，读的人无从复核。
            if PATH_COLUMN_RE.match(column) and PATHLIKE_RE.match(value):
                if not resolve_in_workspace(workspace, value).exists():
                    errors.append(
                        f"LEDGER_PATH_MISSING {name}:{line_number} {column}="
                        f"{value} 指向不存在的文件")

            if column == id_column and not value:
                errors.append(f"LEDGER_BLANK_ID {name}:{line_number} 第一列（{column}）为空")
            elif STATUS_COLUMN_RE.match(column) and not value:
                warnings.append(f"LEDGER_BLANK_STATUS {name}:{line_number} {column} 为空")
            elif OBSERVED_COLUMN_RE.match(column) and not value:
                errors.append(
                    f"LEDGER_BLANK_OBSERVED {name}:{line_number} observed 为空——"
                    "没有实际观测值的「通过项」不构成证据")
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
    homes = parse_home_dirs(args.templates)

    required = set(args.require)
    unknown = required - set(contracts)
    if unknown:
        print(f"FAIL_CONTRACT --require 指定了契约里没有的台账：{sorted(unknown)}")
        return 2

    errors: list[str] = []
    warnings: list[str] = []
    seen: dict[str, dict] = {}

    for name, header in sorted(contracts.items()):
        home = homes.get(name)
        path, strays = locate(workspace, name, home)
        if path is None:
            expected = f"{home}/" if home else "、".join(SEARCH_DIRS)
            line = f"LEDGER_MISSING {name} 不存在（归属目录 {expected}）"
            (errors if name in required else warnings).append(line)
            seen[name] = {"present": False, "home": home}
            continue
        if home and path.parent.name != home:
            warnings.append(
                f"LEDGER_WRONG_LOCATION {name} 不在契约归属目录 {home}/，"
                f"实际在 {path.parent.name}/——本次照它检查，但请挪回归属目录，"
                "否则下一个会话会在归属目录另建一份")
        for stray in strays:
            warnings.append(
                f"LEDGER_STRAY_COPY {name} 在 {stray.parent.name}/ 还有一份同名副本，"
                f"本次只检查 {path.parent.name}/ 的那份——两份并存时，"
                "对副本的更新会被机检静默忽略，请合并后删除多余副本")
        file_errors, file_warnings, count = check_one(name, header, path, workspace)
        errors.extend(file_errors)
        warnings.extend(file_warnings)
        seen[name] = {"present": True, "rows": count, "home": home,
                      "path": path.relative_to(workspace).as_posix(),
                      "stray_copies": [s.relative_to(workspace).as_posix() for s in strays]}

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
