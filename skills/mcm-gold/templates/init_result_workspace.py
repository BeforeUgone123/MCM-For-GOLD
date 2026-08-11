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

# 检索纪律要求这份日志「先于第一次检索」存在——规则原文是「开检索前把白名单、
# 禁入域名和直接 URL 写入」。但此前没有任何一步负责创建它，于是实测四个工作区
# 一个都没有。建工作区时就落一份骨架，把「从零创建」降成「填空」。
# 骨架不复制禁入域名清单：清单在 rules-2026.md，抄一份就会有第二份真相。
SEARCH_LOG_SKELETON = """# 检索日志

检索纪律见 `mcm-gold/references/rules-2026.md` 第五节。**开始任何检索之前**先在这里
写下本次的白名单与直接 URL；每次检索留一条记录。参赛规则第 5 条把「浏览」点名平台
本身列为严重违纪，所以这份日志证明的不是「找到了什么」，而是「没去过哪里」。

未做开放网页检索时也要写一条，注明原因（例如 `research.online=false`）——
空日志与「没做过检索」在事后无法区分。

误开禁入页面：立即关闭，在这里记一条并注明**弃用**，同时记入
`Intermediate-Outputs/RISKS.md`。该页内容不得进入任何产物。
带弃用标记的记录不会被 `verify_search_discipline.py` 判为采用。

| 时间 | 查询/URL | 域名 | 结果 | 采用? | S-id |
|---|---|---|---|---|---|
"""

SEED_FILES = {
    "Reference-Papers/SEARCH_LOG.md": SEARCH_LOG_SKELETON,
}


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

    # 幂等：已存在的骨架文件一律不动，避免覆盖真实记录
    seeded: list[str] = []
    for relative, content in SEED_FILES.items():
        path = result_root / relative
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        seeded.append(relative)

    return {
        "result_root": str(result_root),
        "directories": list(DIRECTORIES),
        "created": created,
        "existing": existing,
        "seeded": seeded,
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
