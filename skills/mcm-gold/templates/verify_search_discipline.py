#!/usr/bin/env python3
"""扫工作区里有没有禁入域名的痕迹。

参赛规则第 5 条把**「浏览」本身**列为严重违反竞赛纪律，并点名了平台。
`rules-2026.md` 的执行条款写得很清楚：误开禁入页面要立即关闭、记入 `SEARCH_LOG.md`
与 `RISKS.md`，**该页内容不得进入任何产物**。

这就给出了一个干净的可机检语义：
  - `SEARCH_LOG.md` / `RISKS.md` 是登记误命中的地方，出现域名合法——但必须带弃用标记，
    否则等于「记了一笔然后照用」；
  - **其余任何产物里出现即为采用**，属取消资格级风险。

此前 T2、T8、adversarial-gates、stage-review-scoring 四处都要求「`SEARCH_LOG.md` 无禁入
域名采用记录」，却没有任何机检——四处要求，零次执行。

域名清单从 `rules-2026.md` 解析，检查器里不抄第二份：官方清单是「包括但不限于」的开放
列举，随时会补充，抄一份就意味着补充完规则、检查还停在旧清单上。**解析不到就报错退出，
绝不当作「没有禁入域名」静默通过**——那正是这类检查最常见的失效方式。

用法：
    python3 verify_search_discipline.py --workspace MCM-Result
    python3 verify_search_discipline.py --workspace MCM-Result --mode rehearsal
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RULES = Path(__file__).resolve().parents[1] / "references" / "rules-2026.md"

DOMAIN_LINE_RE = re.compile(r"^-\s+\*\*禁入域名[^*]*\*\*：(.+)$", re.M)
BACKTICKED_RE = re.compile(r"`([a-z0-9.-]+\.[a-z]{2,})`")

# 登记误命中的专用文件：出现域名是它们的职责
LOG_FILES = {"SEARCH_LOG.md", "RISKS.md"}

# 表示「记了但没用」的标记；缺了就等于记一笔照用
DISCARD_MARKERS = ("弃用", "未采用", "不采用", "不得采用", "误命中", "误开",
                   "已关闭", "排除", "REJECTED", "DISCARDED", "NOT_ADOPTED")

TEXT_SUFFIXES = {".md", ".tex", ".csv", ".txt", ".bib", ".json", ".yaml", ".yml",
                 ".py", ".r", ".m", ".sh"}

SKIP_DIRS = {"Competition-Materials"}      # 官方原件，只读，不由我们负责
CACHE_DIRS = {".venv", "venv", "__pycache__", "node_modules", ".git"}


def parse_forbidden_domains(path: Path) -> list[str]:
    match = DOMAIN_LINE_RE.search(path.read_text(encoding="utf-8"))
    if not match:
        return []
    return sorted(set(BACKTICKED_RE.findall(match.group(1))))


def iter_text_files(root: Path):
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            children = sorted(current.iterdir())
        except OSError:
            continue
        for child in children:
            if child.is_dir():
                if child.name in CACHE_DIRS or child.name in SKIP_DIRS:
                    continue
                stack.append(child)
            elif child.suffix.lower() in TEXT_SUFFIXES:
                yield child


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--rules", type=Path, default=RULES)
    parser.add_argument("--mode", choices=("live", "rehearsal"), default="live",
                        help="rehearsal 下产物里的命中降为 warning："
                             "赛前演练期允许访问历年题归档等，竞赛期间一律不进")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    domains = parse_forbidden_domains(args.rules)
    if not domains:
        # 空清单会让后面每一条比对都通过，报告一片绿——必须显式失败
        print(f"FAIL_CONTRACT 没能从 {args.rules} 解析出禁入域名清单，检查未执行。")
        return 2

    workspace = args.workspace.resolve()
    if not workspace.is_dir():
        print(f"WORKSPACE_NOT_FOUND {workspace}")
        return 2

    errors: list[str] = []
    warnings: list[str] = []
    hits: list[dict] = []

    for path in iter_text_files(workspace):
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        relative = path.relative_to(workspace).as_posix()
        in_log = path.name in LOG_FILES
        for number, line in enumerate(lines, start=1):
            found = [d for d in domains if d in line]
            if not found:
                continue
            marked = any(marker in line for marker in DISCARD_MARKERS)
            record = {"file": relative, "line": number, "domains": found,
                      "in_log": in_log, "discard_marked": marked,
                      "text": line.strip()[:160]}
            hits.append(record)
            if in_log:
                if not marked:
                    warnings.append(
                        f"FORBIDDEN_DOMAIN_UNMARKED {relative}:{number} 记了 "
                        f"{found} 却没有弃用标记——登记的意义是证明没有采用")
            else:
                line_text = (f"FORBIDDEN_DOMAIN_IN_ARTIFACT {relative}:{number} "
                             f"产物里出现禁入域名 {found}。规则原文：误开页面的内容"
                             f"「不得进入任何产物」，参赛规则第 5 条把浏览本身列为严重违纪。")
                (errors if args.mode == "live" else warnings).append(line_text)

    status = "FAIL_CONTRACT" if errors else ("NEEDS_HUMAN" if warnings else "PASS")
    search_log = workspace / "Reference-Papers" / "SEARCH_LOG.md"
    if not search_log.is_file():
        warnings.append(
            "SEARCH_LOG_MISSING 没有 Reference-Papers/SEARCH_LOG.md；"
            "做过任何检索就必须有这份日志，否则无从证明检索纪律")
        if status == "PASS":
            status = "NEEDS_HUMAN"

    report = {"status": status, "mode": args.mode, "domains": domains,
              "hits": hits, "errors": errors, "warnings": warnings}
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                            encoding="utf-8")

    print(f"清单 {len(domains)} 个禁入域名，命中 {len(hits)} 处：{status}")
    for line in errors:
        print(f"  [error]   {line}")
    for line in warnings:
        print(f"  [warning] {line}")
    if not errors and not warnings:
        print(f"  未在任何产物里发现 {domains}")
    if args.out:
        print(f"报告：{args.out}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
