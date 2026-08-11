#!/usr/bin/env python3
"""核对 SOURCE_DATA_MAP.csv 与磁盘上的实际文件。

`SOURCE_DATA_MAP.csv` 是「主张 → 数据文件」的索引，T3 建、T7 维护、T8 审计，
三处 SKILL.md 都要求它登记「实际位置、SHA-256」。此前没有任何机检，后果实测：

  - 四个工作区里三个**根本没有这个文件**，剩下一个只有表头零数据行；
  - 2025D 走完 T0–T8，T8 第 15 条声称「审计 SOURCE_DATA_MAP.csv 的正文图/
    关键表均有真实路径和哈希」，文件不存在，Gate 照样通过。

也就是说这条要求从写下起就没被执行过——与 output-layout.md 里「缓存放
Intermediate-Outputs」那条同一个死法：**写了没机检，于是从未被执行**。

登记哈希而不核对哈希，和把旧代码印进附录、把旧结果打进支撑包是同一类失效：
索引看着完整，指向的东西已经变了。区别只在于这份索引一旦失效，
**所有 claim 的可追溯性一起失效**。

用法：
    python3 verify_evidence_map.py --workspace MCM-Result \\
        [--out MCM-Result/Review-Results/T8_EVIDENCE_MAP.json]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

REQUIRED_COLUMNS = [
    "dataset_id", "kind", "claim_ids", "result_ids", "source_ids",
    "actual_location", "sha256", "access_route", "restriction",
    "license_or_terms", "generated_by", "status", "updated_at",
]

VALID_STATUS = {"VERIFIED", "PENDING", "BLOCKED", "SUPERSEDED"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
RESULT_ID_RE = re.compile(r"\bR-\d+\b")
FIGURE_SUFFIXES = {".pdf", ".png", ".svg", ".jpg", ".jpeg"}

# 占位符没填就是没执行；空字符串同理。单列出来是因为它比哈希写错更常见。
PLACEHOLDERS = {"", "-", "na", "n/a", "none", "tbd", "todo",
                "<sha256>", "<hash>", "xxx", "pending"}


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve(workspace: Path, raw: str) -> Path | None:
    """条目里的路径可能带工作区前缀，也可能不带；两种都认，绝对路径直接用。"""
    raw = raw.strip().replace("\\", "/")
    if not raw:
        return None
    candidate = Path(raw)
    if candidate.is_absolute():
        return candidate
    for base in (workspace, workspace.parent):
        resolved = (base / candidate)
        if resolved.exists():
            return resolved
    return workspace / candidate          # 不存在时回一个可读的路径供报错


def known_result_ids(workspace: Path) -> set[str]:
    ids: set[str] = set()
    jsonl = workspace / "Intermediate-Outputs" / "RESULTS.jsonl"
    if jsonl.exists():
        for line in jsonl.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                ids.add(json.loads(line)["id"])
            except (json.JSONDecodeError, KeyError):
                continue
    markdown = workspace / "Intermediate-Outputs" / "RESULTS.md"
    if markdown.exists():
        ids.update(RESULT_ID_RE.findall(markdown.read_text(encoding="utf-8")))
    return ids


def body_figures(workspace: Path) -> list[Path]:
    figures_dir = workspace / "Data-Figures"
    if not figures_dir.is_dir():
        return []
    return sorted(p for p in figures_dir.rglob("*")
                  if p.is_file() and p.suffix.lower() in FIGURE_SUFFIXES
                  and not p.name.startswith("."))


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--require-figures", action="store_true",
                        help="强制要求每张图都有 figure_source 条目，"
                             "不再只在已有条目时才查（T7/T8 用）")
    args = parser.parse_args()

    workspace: Path = args.workspace.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    rows: list[dict[str, str]] = []

    mapping = workspace / "Intermediate-Outputs" / "SOURCE_DATA_MAP.csv"
    figures = body_figures(workspace)

    if not mapping.exists():
        errors.append(
            f"EVIDENCE_MAP_MISSING 证据映射不存在：{mapping.relative_to(workspace)}"
            "（T3 建、T7 维护、T8 审计；缺它则所有 claim 无法追到数据文件）")
    else:
        with mapping.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            header = reader.fieldnames or []
            rows = [row for row in reader
                    if any((value or "").strip() for value in row.values())]

        missing_columns = [c for c in REQUIRED_COLUMNS if c not in header]
        if missing_columns:
            errors.append(f"EVIDENCE_MAP_HEADER_DRIFT 缺列：{missing_columns}")

        if not rows:
            # 还没画图时空表是正常的；论文图都出来了还空，就是这一步没做。
            level = errors if figures else warnings
            level.append(
                f"EVIDENCE_MAP_EMPTY 映射只有表头、零条目，而 Data-Figures/ "
                f"下已有 {len(figures)} 个图文件")

    known_ids = known_result_ids(workspace)
    mapped_names: set[str] = set()

    for index, row in enumerate(rows, start=2):
        tag = (row.get("dataset_id") or f"第{index}行").strip()

        location_raw = (row.get("actual_location") or "").strip()
        target = resolve(workspace, location_raw)
        if not location_raw:
            errors.append(f"EVIDENCE_PATH_EMPTY {tag} 没有填 actual_location")
        elif target is None or not target.exists():
            errors.append(f"EVIDENCE_PATH_MISSING {tag} 指向不存在的文件：{location_raw}")
        else:
            mapped_names.add(target.name)
            recorded = (row.get("sha256") or "").strip().lower()
            if recorded in PLACEHOLDERS:
                errors.append(f"EVIDENCE_HASH_PLACEHOLDER {tag} 的 sha256 还是占位符：{recorded!r}")
            elif not SHA256_RE.match(recorded):
                errors.append(f"EVIDENCE_HASH_MALFORMED {tag} 的 sha256 不是 64 位十六进制：{recorded!r}")
            else:
                actual = sha256_of(target)
                if actual != recorded:
                    errors.append(
                        f"EVIDENCE_HASH_STALE {tag} 登记的哈希与实际文件不符："
                        f"{location_raw} 实际 {actual[:16]}… 登记 {recorded[:16]}…")

        script_raw = (row.get("generated_by") or "").strip()
        if script_raw and script_raw.lower() not in PLACEHOLDERS:
            script = resolve(workspace, script_raw)
            if script is None or not script.exists():
                warnings.append(f"EVIDENCE_SCRIPT_MISSING {tag} 的 generated_by 不存在：{script_raw}")

        for result_id in RESULT_ID_RE.findall(row.get("result_ids") or ""):
            if known_ids and result_id not in known_ids:
                errors.append(f"EVIDENCE_DANGLING_RESULT_ID {tag} 引用了台账里没有的 {result_id}")

        status = (row.get("status") or "").strip().upper()
        if status not in VALID_STATUS:
            warnings.append(f"EVIDENCE_STATUS_UNKNOWN {tag} 的 status={status!r} 不在 {sorted(VALID_STATUS)}")

    if rows or args.require_figures:
        for figure in figures:
            if figure.name in mapped_names:
                continue
            # 图源表与图同名，任一被登记即视为该图已入映射
            if any(name.rsplit(".", 1)[0] == figure.stem for name in mapped_names):
                continue
            line = f"EVIDENCE_FIGURE_UNMAPPED 图未登记进映射：Data-Figures/{figure.name}"
            (errors if args.require_figures else warnings).append(line)

    status = "FAIL_CONTRACT" if errors else ("NEEDS_HUMAN" if warnings else "PASS")
    report = {
        "status": status,
        "map": str(mapping),
        "entries": len(rows),
        "figures": len(figures),
        "errors": errors,
        "warnings": warnings,
    }

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                            encoding="utf-8")

    print(f"证据映射 {len(rows)} 条，图 {len(figures)} 个：{status}")
    for line in errors:
        print(f"  [error]   {line}")
    for line in warnings:
        print(f"  [warning] {line}")
    if not errors and not warnings:
        print("  每条登记都指向真实文件，哈希与实际内容一致。")
    if args.out:
        print(f"报告：{args.out}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
