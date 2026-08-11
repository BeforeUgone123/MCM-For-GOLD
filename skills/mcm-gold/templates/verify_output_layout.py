#!/usr/bin/env python3
"""校验工作区布局纪律，并生成人类 review 的导航索引 README.md。

存在的理由（实测，不是假想）：
2025C 工作区跑完后 `Data-Scripts/` 是 408 MB / 14652 个文件，其中 407 MB 是 `.venv`，
真实源码只有 16 个。人类打开这个目录第一眼看到的是虚拟环境，源码被淹没；
`Paper-Outputs/paper/` 里 `.aux`/`.log` 与 `.tex` 混放，同样把交付物和构建垃圾混在一起。
`output-layout.md` 早就规定「程序产生的数据、缓存和日志放入 Intermediate-Outputs/」，
但这条规定此前没有任何机检，于是从来没被执行过。本脚本把它变成可证伪的断言。

这也不只是整洁问题。Trehan & Chopra 在四次自主研究尝试中记录的失败模式之一是
long-horizon 任务里的记忆退化，其直接诱因就是「LLM 生成的文件越来越多、无人管理」
（arXiv:2601.03315 §3.3）。目录失序会同时拖垮人类 review 和 agent 自身的定位能力。

设计约束（沿用 verify_reference_papers.py 的教训）：
- 只检查**能被证伪的事实**：某类文件在不在某个目录下、一级目录名是否越界、
  索引内容与实际扫描结果是否一致。不判断「这个图画得好不好」这类脚本无从知道的事。
- 不制造新规则去凑检查项。图源 CSS 与图同名同目录（F-001-*.pdf / F-001-*.csv）本身是
  清楚的，不强行要求分目录——高误报的门禁会训练人忽略警告。
- 索引只做**导航**，不复制别处的内容。复制会带来不一致，而不一致的索引比没有索引更糟。
- 索引正文只写事实（路径、存在性、计数、状态），不写生成时间与文件大小，
  否则每次重编译 PDF 都会「过期」，警告变噪音。时间戳放末尾签名行，比对时排除。

用法：
    # 生成/刷新索引（T8 出包前，或任何想让人类 review 的时刻）
    python3 verify_output_layout.py --workspace MCM-Result --write-index

    # 只校验（CI / 终检；索引与实际不符即 REVIEW_INDEX_STALE）
    python3 verify_output_layout.py --workspace MCM-Result \
        --output MCM-Result/Review-Results/T8_OUTPUT_LAYOUT.json
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

CANONICAL_DIRS = (
    "Reference-Papers",
    "Data-Scripts",
    "Competition-Materials",
    "Paper-Outputs",
    "Data-Figures",
    "Intermediate-Outputs",
    "Review-Results",
)

# 缓存/环境目录：按 output-layout.md 属于「程序产生的缓存」，只允许在 Intermediate-Outputs 下。
CACHE_DIR_NAMES = {".venv", "venv", "__pycache__", "node_modules", ".pytest_cache",
                   ".ipynb_checkpoints", ".mypy_cache", ".ruff_cache"}
CACHE_FILE_SUFFIXES = {".pyc", ".pyo"}

# LaTeX / 构建中间产物：属于日志与缓存，不该混在交付目录里。
BUILD_SUFFIXES = {".aux", ".log", ".out", ".toc", ".lof", ".lot", ".fls",
                  ".fdb_latexmk", ".synctex.gz", ".bbl", ".blg", ".nav",
                  ".snm", ".vrb", ".xdv"}

INDEX_NAME = "README.md"
SIGNATURE_PREFIX = "<!-- generated-by:"


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def walk_pruned(base: Path):
    """深度优先遍历，命中缓存目录就把它整个折叠掉，不再下钻。

    必须手写而不能用 rglob：一个 .venv 里有上千个 __pycache__，全列出来会让报告
    变成几万行噪音，人类反而看不见「有个 .venv 在源码目录里」这一条真正的结论。
    yield (path, is_pruned_cache_dir)。
    """
    stack = [base]
    while stack:
        current = stack.pop()
        try:
            children = sorted(current.iterdir())
        except OSError:
            continue
        for child in children:
            if child.is_dir():
                if child.name in CACHE_DIR_NAMES:
                    yield child, True      # 折叠：报这一条，不看里面
                else:
                    stack.append(child)
                    yield child, False
            else:
                yield child, False


def scan_cache_pollution(root: Path) -> list[str]:
    """在 Intermediate-Outputs 之外找缓存目录与编译产物。返回相对路径，已折叠到目录级。"""
    hits: list[str] = []
    exempt = root / "Intermediate-Outputs"
    for name in CANONICAL_DIRS:
        base = root / name
        if not base.is_dir() or base == exempt:
            continue
        for path, pruned in walk_pruned(base):
            if pruned:
                hits.append(rel(path, root) + "/")
            elif path.is_file() and path.suffix in CACHE_FILE_SUFFIXES:
                hits.append(rel(path, root))
    return sorted(set(hits))


def scan_build_artifacts(root: Path) -> list[str]:
    """交付目录里的 LaTeX/构建中间产物。"""
    hits: list[str] = []
    for name in ("Paper-Outputs", "Data-Figures"):
        base = root / name
        if not base.is_dir():
            continue
        for path, pruned in walk_pruned(base):
            if pruned or not path.is_file():
                continue
            # .synctex.gz 是双后缀，suffix 只给 .gz
            joined = "".join(path.suffixes[-2:])
            if path.suffix in BUILD_SUFFIXES or joined in BUILD_SUFFIXES:
                hits.append(rel(path, root))
    return sorted(set(hits))


def scan_extra_dirs(root: Path) -> list[str]:
    return sorted(
        p.name for p in root.iterdir()
        if p.is_dir() and p.name not in CANONICAL_DIRS and not p.name.startswith(".")
    )


# 各题标题里都可能出现的通用词，不能当作某一题的指纹
GENERIC_TERMS = frozenset({
    "模型", "方案", "策略", "方法", "分析", "优化", "问题", "确定", "选择",
    "判定", "研究", "设计", "评价", "预测", "控制", "系统", "数据", "计算",
    "求解", "算法", "建模", "决策", "规划", "识别", "检测", "估计", "仿真",
})

TITLE_RE = re.compile(r"\\title\{([^}]*)\}")
CJK_RUN_RE = re.compile(r"[\u4e00-\u9fff]{2,}")


def _paper_title(workspace: Path) -> str:
    main_tex = workspace / "Paper-Outputs" / "paper" / "main.tex"
    if not main_tex.is_file():
        return ""
    match = TITLE_RE.search(main_tex.read_text(encoding="utf-8", errors="ignore"))
    if not match:
        return ""
    return re.sub(r"\\[A-Za-z]+\s*", "", match.group(1)).strip()


def _bigrams(text: str) -> set[str]:
    grams: set[str] = set()
    for run in CJK_RUN_RE.findall(text):
        for i in range(len(run) - 1):
            grams.add(run[i:i + 2])
    return grams


def _paper_corpus(workspace: Path) -> str:
    paper_dir = workspace / "Paper-Outputs" / "paper"
    if not paper_dir.is_dir():
        return ""
    return "\n".join(p.read_text(encoding="utf-8", errors="ignore")
                     for p in sorted(paper_dir.glob("*.tex")))


def _problem_statement(workspace: Path) -> str:
    """官方赛题原文。`cumcm-*` 是各题共有的规则/格式文件，不是题目内容。"""
    materials = workspace / "Competition-Materials"
    if not materials.is_dir():
        return ""
    chunks: list[str] = []
    for path in sorted(materials.iterdir()):
        if not path.is_file() or path.name.startswith("cumcm-"):
            continue
        suffix = path.suffix.lower()
        if suffix in {".md", ".txt"}:
            chunks.append(path.read_text(encoding="utf-8", errors="ignore"))
        elif suffix == ".pdf":
            try:
                proc = subprocess.run(["pdftotext", "-q", str(path), "-"],
                                      capture_output=True, text=True, timeout=60)
                chunks.append(proc.stdout)
            except (OSError, subprocess.SubprocessError):
                continue
    return "\n".join(chunks)


def _bigram_counts(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for run in CJK_RUN_RE.findall(text):
        for i in range(len(run) - 1):
            gram = run[i:i + 2]
            counts[gram] = counts.get(gram, 0) + 1
    return counts


TOPIC_TERMS_NAME = "TOPIC_TERMS.txt"
PROBLEM_MIN = 5          # 生成候选词时，在赛题里至少出现这么多次
FOREIGN_MIN_TERMS = 2    # 词是人确认过的，两个不同词同时出现已经很难是巧合
FOREIGN_MIN_TOTAL = 5


def read_topic_terms(workspace: Path) -> list[str]:
    """读本题的专属词表：`Competition-Materials/TOPIC_TERMS.txt`，一行一词，# 开头为注释。"""
    path = workspace / "Competition-Materials" / TOPIC_TERMS_NAME
    if not path.is_file():
        return []
    terms = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.split("#", 1)[0].strip()
        if len(line) >= 2:
            terms.append(line)
    return terms


def suggest_topic_terms(workspace: Path, limit: int = 20) -> list[tuple[str, int]]:
    """从官方赛题原文里挑候选专属词，供人删减后写进 TOPIC_TERMS.txt。

    只挑「在本题赛题里高频、在兄弟题赛题里一次不出现」的 2-gram。这一步只做建议，
    不自动落盘：候选里混着「文件」「网络」这类词，必须人过一遍。
    """
    if shutil.which("pdftotext") is None:
        return []
    own = _bigram_counts(_problem_statement(workspace))
    if not own:
        return []
    others = []
    for candidate in sorted(workspace.parent.iterdir()):
        if not candidate.is_dir() or candidate.resolve() == workspace.resolve():
            continue
        text = _problem_statement(candidate)
        if text.strip():
            others.append(_bigram_counts(text))
    ranked = [(g, n) for g, n in own.items()
              if n >= PROBLEM_MIN and g not in GENERIC_TERMS
              and all(o.get(g, 0) == 0 for o in others)]
    return sorted(ranked, key=lambda kv: -kv[1])[:limit]


def scan_foreign_topic(root: Path) -> tuple[list[dict], str]:
    """检查论文正文里有没有混进兄弟工作区那道题的内容。

    同机常有 `MCM-Result-2025B/`、`MCM-Result-2025D/` 这样的并存工作区，而 shell 的
    当前目录跨命令持久。实测事故：给 2025D 补写章节时 cwd 仍停在 2025B，一整节矿井
    突水的内容被写进了 2025B 的论文并连带重编译。路径合法、结构合法、契约照过——
    当时靠「编译出的页数与预期对不上」才发现，没有任何检查拦得住。

    词表由人确认，不自动推断。三种自动指纹都实测失败过：
    标题 2-gram 复现真实事故时一条没命中（写错进去的整节讲「巷道」「矿工」，标题里
    没有）；论文正文 2-gram 挑出的是「题面」「依赖」「入口」这类**作者措辞习惯**词；
    赛题原文 2-gram 已经能挑出「巷道」「突水」「碳化硅」这些真名词，但仍混进「文件」
    「段数」「点的」，在四个真实工作区上三个误报。
    本文件开头就写着「高误报的门禁会训练人忽略警告」——所以这里改成 `--suggest-topic-terms`
    出候选、人删减后落盘 `Competition-Materials/TOPIC_TERMS.txt`，检查只用确认过的词。
    T0 本来就要精读赛题，挑五六个专属名词是顺手的事，换来的是零误报。

    返回 (命中列表, 状态)。没有词表就 SKIPPED，不假装检查过。
    """
    own_terms = set(read_topic_terms(root))
    own_body = _paper_corpus(root)
    if not own_body:
        return [], "SKIPPED_NO_PAPER"
    if not own_terms:
        return [], "SKIPPED_NO_TOPIC_TERMS"

    hits: list[dict] = []
    for sibling in sorted(root.parent.iterdir()):
        if not sibling.is_dir() or sibling.resolve() == root:
            continue
        foreign_terms = [t for t in read_topic_terms(sibling) if t not in own_terms]
        found = {t: own_body.count(t) for t in foreign_terms if t in own_body}
        total = sum(found.values())
        if not found:
            continue
        # 分两档：整节写错工作区会同时带进好几个专属词、几十次命中，那是 error；
        # 零星一两次可能是正文里正当地提了一句别的场景，只提示不阻断。
        # 实测：一整节 2025D 内容写进 2025B 会命中「巷道 14、逃生 5、突水 4」，
        # 而只写进 12 行时总共才 3 次——所以低档不能没有。
        level = ("error" if len(found) >= FOREIGN_MIN_TERMS
                 and total >= FOREIGN_MIN_TOTAL else "warning")
        hits.append({
            "sibling": sibling.name,
            "sibling_title": _paper_title(sibling),
            "matched": found,
            "total": total,
            "level": level,
        })
    return hits, "CHECKED"


def _first_existing(root: Path, *candidates: str) -> str | None:
    for c in candidates:
        if (root / c).exists():
            return c
    return None


def _read_contract_status(root: Path) -> tuple[str | None, str]:
    """返回 (契约文件相对路径, 状态描述)。文件缺失必须可见，不是省略。"""
    path = root / "Review-Results" / "T7_PAPER_CONTRACT.json"
    if not path.is_file():
        return None, "未生成"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        return rel(path, root), f"无法解析（{exc.__class__.__name__}）"
    status = data.get("status", "无 status 字段")
    errs = data.get("errors")
    warns = data.get("warnings")
    detail = f"`{status}`"
    if isinstance(errs, list) and isinstance(warns, list):
        detail += f"，error {len(errs)} / warning {len(warns)}"
    return rel(path, root), detail


def collect(root: Path) -> dict:
    """扫描出索引与校验共用的事实。两者共用同一份数据，保证索引不会与检查结论矛盾。"""
    figures: list[dict] = []
    figdir = root / "Data-Figures"
    if figdir.is_dir():
        for fig in sorted(figdir.glob("*.pdf")):
            source = fig.with_suffix(".csv")
            figures.append({
                "figure": rel(fig, root),
                "source_table": rel(source, root) if source.is_file() else None,
            })

    scripts: list[str] = []
    sdir = root / "Data-Scripts"
    if sdir.is_dir():
        scripts = sorted(
            rel(p, root) for p, pruned in walk_pruned(sdir)
            if not pruned and p.is_file() and p.suffix not in CACHE_FILE_SUFFIXES
        )

    contract_path, contract_status = _read_contract_status(root)
    return {
        "reader_pdf": _first_existing(
            root, "Paper-Outputs/paper/main.pdf",
            "Paper-Outputs/deliverables/print/paper.pdf"),
        "submission_pdf": _first_existing(
            root, "Paper-Outputs/deliverables/submission/paper.pdf",
            "Paper-Outputs/paper/main_submission.pdf"),
        "support_zip": _first_existing(
            root, "Paper-Outputs/deliverables/submission/support.zip"),
        "figures": figures,
        "scripts": scripts,
        "evidence_ledger": _first_existing(
            root, "Intermediate-Outputs/RESULTS.md",
            "Intermediate-Outputs/RESULTS_LEDGER.md",
            "Review-Results/RESULTS_LEDGER.csv"),
        "coverage_ledger": _first_existing(
            root, "Review-Results/PAPER_COVERAGE_LEDGER.csv"),
        "contract": contract_path,
        "contract_status": contract_status,
        "state": _first_existing(root, "Intermediate-Outputs/STATE.md"),
        "decisions": _first_existing(root, "Intermediate-Outputs/DECISIONS.md"),
        "signoffs": _first_existing(root, "Intermediate-Outputs/HUMAN_SIGNOFFS.md"),
        "run_entry": _first_existing(root, "Data-Scripts/run_all.py"),
    }


def _row(label: str, path: str | None) -> str:
    if path is None:
        return f"| {label} | — | **未生成** |"
    return f"| {label} | `{path}` | 有 |"


def render_index(root: Path, facts: dict) -> str:
    """只做导航：指路 + 存在性 + 计数。不复制别处内容，避免两处不一致。"""
    lines: list[str] = [
        f"# {root.name} · review 从这里开始",
        "",
        "> 本文件由 `verify_output_layout.py --write-index` 扫描实际文件生成，**不要手改**；",
        "> 手改会在下次校验时报 `REVIEW_INDEX_STALE`。它只负责指路，内容以被指向的文件为准。",
        "",
        "## 1. 成品：人类要看的就这几件",
        "",
        "| 产物 | 路径 | 状态 |",
        "|---|---|---|",
        _row("论文·阅读版 PDF", facts["reader_pdf"]),
        _row("论文·提交版 PDF", facts["submission_pdf"]),
        _row("支撑材料包", facts["support_zip"]),
        "",
    ]

    figures = facts["figures"]
    if figures:
        missing = sum(1 for f in figures if f["source_table"] is None)
        lines.append(f"### 正文图 {len(figures)} 张"
                     + ("（每张都配有图源表）" if not missing
                        else f"（**{missing} 张缺图源表**）"))
        lines.append("")
        lines.append("| 图 | 图源表（可核对数值） |")
        lines.append("|---|---|")
        for f in figures:
            src = f"`{f['source_table']}`" if f["source_table"] else "**缺失**"
            lines.append(f"| `{f['figure']}` | {src} |")
    else:
        lines.append("### 正文图：**无**（`Data-Figures/` 下没有 PDF 图）")
    lines += ["", "## 2. 结论怎么核", "",
              "| 用途 | 路径 |", "|---|---|"]
    lines.append(_row_plain("每个数值由哪段代码产生", facts["evidence_ledger"]))
    lines.append(_row_plain("论文每问覆盖了哪些要求", facts["coverage_ledger"]))
    lines.append(_row_plain(f"终检契约（{facts['contract_status']}）", facts["contract"]))
    lines.append("")
    if facts["run_entry"]:
        lines += ["复现全部结果：", "",
                  "```bash",
                  f"cd {Path(facts['run_entry']).parent.as_posix()} && "
                  "python3 run_all.py --all --seed <见 STATE.md>",
                  "```", ""]
    else:
        lines += ["复现入口 `Data-Scripts/run_all.py` **未生成**。", ""]

    lines += [
        "## 3. 过程：要追溯时才看",
        "",
        "| 内容 | 路径 |",
        "|---|---|",
        _row_plain("状态与阶段结论", facts["state"]),
        _row_plain("决策记录（选了什么、否了什么）", facts["decisions"]),
        _row_plain("人工签署位", facts["signoffs"]),
        f"| 源码（{len(facts['scripts'])} 个文件） | `Data-Scripts/` |",
        "| 运行日志与中间数据 | `Intermediate-Outputs/` |",
        "| 环境缓存（不必看） | `Intermediate-Outputs/venv/` |",
        "",
    ]
    return "\n".join(lines) + "\n"


def _row_plain(label: str, path: str | None) -> str:
    return f"| {label} | " + (f"`{path}` |" if path else "**未生成** |")


def strip_signature(text: str) -> str:
    return "".join(
        line for line in text.splitlines(keepends=True)
        if not line.startswith(SIGNATURE_PREFIX)
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="校验工作区布局并生成 review 导航索引")
    parser.add_argument("--workspace", type=Path, required=True,
                        help="工作区根目录（含七个一级目录）")
    parser.add_argument("--write-index", action="store_true",
                        help=f"生成/刷新 {INDEX_NAME}；不加则只校验")
    parser.add_argument("--output", type=Path, default=None, help="JSON 报告落盘路径")
    parser.add_argument("--suggest-topic-terms", action="store_true",
                        help=f"从官方赛题原文挑题目专属词候选，供人删减后写进 "
                             f"Competition-Materials/{TOPIC_TERMS_NAME}")
    args = parser.parse_args()

    root = args.workspace.resolve()

    if args.suggest_topic_terms:
        candidates = suggest_topic_terms(root)
        if not candidates:
            print("没能生成候选：需要 pdftotext，且 Competition-Materials/ 下要有"
                  "非 cumcm-* 的赛题原文，同级还要有别的工作区可比。")
            return 2
        print(f"# {root.name} 的题目专属词候选（在本题赛题高频、兄弟题赛题零命中）")
        print(f"# 删掉通用词后存为 Competition-Materials/{TOPIC_TERMS_NAME}，一行一个")
        for term, count in candidates:
            print(f"{term}    # 赛题中 {count} 次")
        return 0
    report: dict = {"schema_version": 1, "workspace": str(root)}
    errors: list[str] = []
    warnings: list[str] = []

    if not root.is_dir():
        report["status"] = "WORKSPACE_NOT_FOUND"
        report["errors"] = [f"WORKSPACE_NOT_FOUND 工作区不存在：{root}"]
        emit(report, args.output)
        return 2

    missing_dirs = [d for d in CANONICAL_DIRS if not (root / d).is_dir()]
    report["canonical_dirs"] = {"expected": list(CANONICAL_DIRS), "missing": missing_dirs}
    if missing_dirs:
        warnings.append(
            "CANONICAL_DIR_MISSING 缺少约定目录：" + "、".join(missing_dirs)
            + "。用 init_result_workspace.py 幂等补齐。"
        )

    extra = scan_extra_dirs(root)
    report["extra_top_level_dirs"] = extra
    if extra:
        errors.append(
            "UNKNOWN_TOP_LEVEL_DIR 出现约定之外的一级目录：" + "、".join(extra)
            + "。output-layout.md 规定不得增加第八个一级目录；"
              "请并入七个目录之一，或说明为何必须破例。"
        )

    cache = scan_cache_pollution(root)
    report["cache_outside_intermediate"] = cache
    if cache:
        errors.append(
            "CACHE_IN_SOURCE_TREE 缓存/虚拟环境出现在源码或交付目录下："
            + "、".join(cache[:8]) + ("…" if len(cache) > 8 else "")
            + "。output-layout.md 规定程序产生的缓存归 Intermediate-Outputs/；"
              "虚拟环境放 Intermediate-Outputs/venv/。"
              "实测一个 .venv 就能让源码目录从 16 个文件涨到 14652 个，人类无法 review。"
        )

    foreign, foreign_status = scan_foreign_topic(root)
    report["foreign_topic_hits"] = foreign
    report["foreign_topic_scan"] = foreign_status
    if foreign_status == "SKIPPED_NO_TOPIC_TERMS":
        warnings.append(
            f"TOPIC_TERMS_MISSING 没有 Competition-Materials/{TOPIC_TERMS_NAME}，"
            "跨工作区串题检查未执行。跑 --suggest-topic-terms 出候选，"
            "删掉「文件」「网络」这类通用词后落盘即可。")
    for hit in foreign:
        sample = "、".join(f"{g}×{n}" for g, n in
                           sorted(hit["matched"].items(), key=lambda kv: -kv[1])[:6])
        line = (
            f"FOREIGN_TOPIC_CONTENT 论文正文出现兄弟工作区 {hit['sibling']}"
            f"（《{hit['sibling_title']}》）的题目专属词：{sample}，共 {hit['total']} 次。"
            "多工作区并存时 shell 的 cwd 跨命令持久，写文件用相对路径极易落到隔壁题目上；"
            "实测发生过一整节内容写错工作区并连带重编译，路径与结构全部合法、无一检查报警。"
            "先核对这几处正文属于哪道题，确认无误再豁免。"
        )
        (errors if hit["level"] == "error" else warnings).append(line)

    build = scan_build_artifacts(root)
    report["build_artifacts_in_deliverables"] = build
    if build:
        errors.append(
            "BUILD_ARTIFACT_IN_DELIVERABLE 交付目录下混有构建中间产物："
            + "、".join(build[:8]) + ("…" if len(build) > 8 else "")
            + "。LaTeX 的 .aux/.log 等属于日志，应写到 Intermediate-Outputs/；"
              "混在 Paper-Outputs/ 里会随交付物一起被打包或被人类误读为正式产物。"
        )

    facts = collect(root)
    report["facts"] = facts

    # 证据台账缺失：只在论文已产出时才算缺陷——刚初始化的空工作区没有台账是正常的，
    # 在那里报错属于误报。但论文都写完了还没有台账，就意味着论文里的每个数值都没有
    # 可机读的来源记录：人无法核对，机器也无法验「论文数值 == 运行结果」
    # （格式规范第五条红线）。2025C 实测踩中：台账被写到了会话临时目录，
    # 跑完随之消失，工作区里论文在、台账不在，契约当时读到的 12 行已无处可查。
    if facts["evidence_ledger"] is None:
        if facts["reader_pdf"]:
            errors.append(
                "EVIDENCE_LEDGER_MISSING 论文已产出，但工作区里没有结果台账"
                "（Intermediate-Outputs/RESULTS.md）。论文中的数值因此没有可机读的来源，"
                "无法核对，也无法机检「运行结果与论文相符」。"
                "常见原因：run_all.py 的 STATE_DIR 默认相对 cwd 的 workspace/，"
                "从别处调用会把台账写到工作区之外——"
                "跑时显式设 MCM_STATE_DIR 指向 Intermediate-Outputs/。"
            )
        else:
            warnings.append(
                "EVIDENCE_LEDGER_ABSENT 还没有结果台账（论文也尚未产出，属正常早期状态）。"
            )

    rendered = render_index(root, facts)

    index_path = root / INDEX_NAME
    if args.write_index:
        stamp = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
        index_path.write_text(
            rendered + f"{SIGNATURE_PREFIX} verify_output_layout.py at {stamp} -->\n",
            encoding="utf-8")
        report["index"] = {"status": "WRITTEN", "path": rel(index_path, root)}
    elif not index_path.is_file():
        report["index"] = {"status": "MISSING", "path": INDEX_NAME}
        warnings.append(
            f"REVIEW_INDEX_MISSING 工作区根没有 {INDEX_NAME}，人类 review 没有入口。"
            f"跑 `--write-index` 生成。"
        )
    else:
        on_disk = strip_signature(index_path.read_text(encoding="utf-8"))
        if on_disk != strip_signature(rendered):
            report["index"] = {"status": "STALE", "path": INDEX_NAME}
            errors.append(
                f"REVIEW_INDEX_STALE {INDEX_NAME} 与实际文件不符（产物增删或被手改）。"
                f"跑 `--write-index` 重新生成；过期的索引比没有索引更容易误导 review。"
            )
        else:
            report["index"] = {"status": "FRESH", "path": INDEX_NAME}

    report["errors"] = errors
    report["warnings"] = warnings
    report["status"] = "FAIL" if errors else ("PASS_WITH_WARNINGS" if warnings else "PASS")
    emit(report, args.output)
    return 1 if errors else 0


def emit(report: dict, output: Path | None) -> None:
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    sys.exit(main())
