#!/usr/bin/env python3
"""比对正文修订前后两个版本，拦住润色悄悄改掉的东西。

用 AI 润色、降重或"拟人化"改写正文，是当前最常见的一类操作，也是当前
**唯一没有机检的**一类：T7 只有「不得用流畅语言隐藏证据缺口」这样的文字
约束，而实测表明文字约束拦不住。

2025D 实测（60 段经本地 7B 模型改写，段落级已有占位符/数字/语言/长度四道闸）：

  - 数字被改 1 处，段落级闸拦住了；
  - **范围号 `--` 被改成 `:` 4 处**——`$15$--$198$ \\si{m}`（15 到 198 米）
    变成 `$15$:$198$(\\si{m})`（读作 15 比 198）。数字没变、结构没变，
    四道闸一道没响，因为它改的是占位符**之间**的纯文本标点；
  - **判断被弱化 5 处**——"突水起点会凭空移动近 200 m" 变成 "可能会出现…移动"，
    确定结论降级为可能性；
  - 明令禁止的模板连接词净增 18 次（因此 +12、首先 +2、其次 +1…）；
  - 中文正文新增半角标点 9 处；
  - 句长标准差 20.4 → 17.8：节奏反而更均匀了，而句长方差小正是 AI 文本的特征。
    也就是说，以"降 AI 率"为目的的改写，实测把 AI 味改重了。

结论：润色不可假定为改进，必须前后对比取证。数字守恒是最低门槛而不是充分条件。

用法：
    python3 verify_prose_revision.py --before paper/ --after paper-revised/ \\
        [--out Review-Results/T7_PROSE_REVISION.json]
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")
RANGE_DASH_RE = re.compile(r"(?<!-)--(?!-)")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")

# 模糊限定词：确定的结论被降级成可能性，是润色最隐蔽的一种破坏
HEDGES = ("可能", "或许", "大约", "一般来说", "通常", "往往",
          "在一定程度上", "可以认为", "似乎", "基本上")

# 模板连接词：AI 文本的显著标记，人写的论文用得远没有这么密
TEMPLATE_CONNECTIVES = ("首先", "其次", "然后", "因此", "此外", "另外", "同时，",
                        "综上所述", "总而言之", "总之", "值得注意的是",
                        "需要指出的是", "可以看出", "由此可见")

# 中文正文里的半角标点属于格式退化
HALFWIDTH = "();,"

LATEX_CMD_RE = re.compile(r"\\[A-Za-z]+\*?(?:\[[^\]]*\])?")
MATH_RE = re.compile(r"\$[^$]*\$")
SENT_SPLIT_RE = re.compile(r"[。；！？\n]")


def normalize(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def prose_only(text: str) -> str:
    """剥掉 LaTeX 命令与数学环境，只留下人读的那部分。"""
    text = MATH_RE.sub(" ", text)
    text = LATEX_CMD_RE.sub(" ", text)
    return text.replace("{", " ").replace("}", " ")


def sentence_lengths(text: str) -> list[int]:
    return [len(s.strip()) for s in SENT_SPLIT_RE.split(prose_only(text))
            if len(s.strip()) >= 4]


def rhythm(text: str) -> tuple[int, float, float]:
    lengths = sentence_lengths(text)
    if len(lengths) < 2:
        return len(lengths), 0.0, 0.0
    return len(lengths), statistics.mean(lengths), statistics.pstdev(lengths)


def count_all(text: str, needles: tuple[str, ...]) -> Counter:
    return Counter({w: text.count(w) for w in needles if text.count(w)})


def compare_file(before: str, after: str) -> dict:
    before, after = normalize(before), normalize(after)
    findings: list[dict] = []

    # --- 错误级：改变了论文陈述的事实
    a, b = Counter(NUMBER_RE.findall(before)), Counter(NUMBER_RE.findall(after))
    if a != b:
        diff = (a - b) + (b - a)
        findings.append({
            "code": "NUMBER_DRIFT", "level": "error",
            "detail": {k: v for k, v in sorted(diff.items())},
        })

    da, db = len(RANGE_DASH_RE.findall(before)), len(RANGE_DASH_RE.findall(after))
    if da != db:
        findings.append({
            "code": "RANGE_DASH_DRIFT", "level": "error",
            "detail": {"before": da, "after": db},
        })

    pa = prose_only(before)
    pb = prose_only(after)
    hedge_delta = {w: n for w, n in
                   ((w, pb.count(w) - pa.count(w)) for w in HEDGES) if n > 0}
    if hedge_delta:
        findings.append({
            "code": "HEDGE_INFLATION", "level": "error",
            "detail": hedge_delta,
        })

    # --- 警告级：没改事实，但让文本更像机器写的
    conn_delta = {w: n for w, n in
                  ((w, pb.count(w) - pa.count(w)) for w in TEMPLATE_CONNECTIVES)
                  if n > 0}
    if conn_delta:
        findings.append({
            "code": "TEMPLATE_CONNECTIVE_INFLATION", "level": "warning",
            "detail": conn_delta,
        })

    if CJK_RE.search(pb):
        half = {ch: pb.count(ch) - pa.count(ch) for ch in HALFWIDTH
                if pb.count(ch) - pa.count(ch) > 0}
        if half:
            findings.append({
                "code": "HALFWIDTH_PUNCT", "level": "warning",
                "detail": half,
            })

    na, ma, sa = rhythm(before)
    nb, mb, sb = rhythm(after)
    if sa > 0 and sb < sa * 0.95:
        findings.append({
            "code": "RHYTHM_FLATTENED", "level": "warning",
            "detail": {"stdev_before": round(sa, 1), "stdev_after": round(sb, 1),
                       "mean_before": round(ma, 1), "mean_after": round(mb, 1)},
        })

    return {
        "findings": findings,
        "sentences": {"before": na, "after": nb},
        "rhythm": {"stdev_before": round(sa, 1), "stdev_after": round(sb, 1)},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--before", type=Path, required=True, help="修订前的正文目录")
    ap.add_argument("--after", type=Path, required=True, help="修订后的正文目录")
    ap.add_argument("--pattern", default="*.tex")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    errors: list[str] = []
    warnings: list[str] = []
    per_file: dict[str, dict] = {}

    befores = sorted(args.before.glob(args.pattern))
    if not befores:
        print(f"FAIL_CONTRACT 修订前目录没有匹配 {args.pattern} 的文件：{args.before}")
        return 2

    for path in befores:
        target = args.after / path.name
        if not target.exists():
            errors.append(f"REVISION_FILE_MISSING 修订后缺少 {path.name}")
            continue
        result = compare_file(path.read_text(encoding="utf-8"),
                              target.read_text(encoding="utf-8"))
        per_file[path.name] = result
        for finding in result["findings"]:
            line = f"{finding['code']} {path.name} {finding['detail']}"
            (errors if finding["level"] == "error" else warnings).append(line)

    status = "FAIL_CONTRACT" if errors else ("NEEDS_HUMAN" if warnings else "PASS")
    report = {"status": status, "errors": errors, "warnings": warnings,
              "files": per_file}

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                            encoding="utf-8")

    print(f"比对 {len(per_file)} 个文件：{status}")
    for line in errors:
        print(f"  [error]   {line}")
    for line in warnings:
        print(f"  [warning] {line}")
    if not errors and not warnings:
        print("  修订未改动数字、范围号、判断强弱，也没有让节奏变均匀。")
    else:
        print("\n警告不阻断，但必须逐条看过再决定采不采纳这一版修订——"
              "润色不可假定为改进。")
    if args.out:
        print(f"报告：{args.out}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
