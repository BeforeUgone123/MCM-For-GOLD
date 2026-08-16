#!/usr/bin/env python3
"""Verify T7/T8 paper coverage, rubric, and reader/submission closure."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from difflib import SequenceMatcher
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable


COVERAGE_COLUMNS = [
    "question_id",
    "component",
    "required_content",
    "claim_or_risk_ids",
    "paper_anchor",
    "evidence_ids",
    "observed",
    "status",
    "human_status",
]
COMPONENTS = {
    "interface",
    "definition",
    "algorithm",
    "result",
    "validation",
    "boundary",
}
NON_NA_COMPONENTS = {"interface", "definition", "algorithm", "result"}
RUBRIC = {
    "摘要页": (15, 10),
    "问题分析与假设": (10, 6),
    "模型建立": (25, 16),
    "求解与结果正确性": (22, 15),
    "检验与稳健性": (13, 8),
    "写作与图表": (12, 8),
    "合规与附录": (3, 3),
}
RUBRIC_COLUMNS = [
    "dimension",
    "score",
    "max_score",
    "pass_score",
    "evidence",
    "observed",
    "status",
]
CODE_SUFFIXES = {
    ".py",
    ".r",
    ".m",
    ".jl",
    ".java",
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
    ".sh",
    ".sql",
}
ID_SUFFIX = r"[A-Z0-9]+(?:-[A-Z0-9]+)*"
ID_RE = re.compile(rf"\b[CK]-{ID_SUFFIX}\b", re.IGNORECASE)
RISK_ID_RE = re.compile(rf"\bK-{ID_SUFFIX}\b", re.IGNORECASE)
# 检验证据的两个载体：R-（RESULTS.md 的运行记录）与 P-（REVIEW_PASS_ITEMS.csv 的验收项）。
# V- 保留只为兼容历史工作区：它曾被三处文档要求回填，却没有任何台账签发，
# 契约文档已改回 R/P，这里继续放行旧数据但不再宣传。
VALIDATION_ID_RE = re.compile(rf"\b(?:R|P|V)-{ID_SUFFIX}\b", re.IGNORECASE)
DECISION_ID_RE = re.compile(rf"\bD-{ID_SUFFIX}\b", re.IGNORECASE)
CJK_RE = re.compile(r"[一-鿿]")
EQUATION_NUMBER_RE = re.compile(r"[（(]\s*\d+(?:\.\d+)?\s*[)）]\s*$")
TABLE_LABEL_RE = re.compile(r"表\s*(\d+(?:[-–.]\d+)?)")
FIGURE_LABEL_RE = re.compile(r"图\s*(\d+(?:[-–.]\d+)?)")
REFERENCE_ENTRY_RE = re.compile(r"^\s*\[\d+\]", re.MULTILINE)
UNIT_VALUE_RE = re.compile(
    r"\d+(?:\.\d+)?(?:\s*[×xX]\s*10[−–\-]?\d+)?\s*(?:"
    r"µm|μm|um|nm|mm|cm|dm|km|kg|mg|kWh|kHz|MHz|GHz|Hz|kPa|MPa|GPa|Pa|kW|MW|kV|mV|mA"
    r"|mol|min|rad|dB|lm|lx|km/h|m/s|°|◦|℃|%|‰"
    r"|平方米|立方米|平方千米|千瓦时|摄氏度|毫米汞柱|毫升|微米|纳米|毫米|厘米|千米|公里|千克"
    r"|万元|万吨|小时|分钟|米|克|吨|升|度|秒|天|年|月|日|个|件|台|次|倍|元|人|组|种|类|条|篇|页|行|字|万"
    r"|[sgNtJWVAKmth](?![A-Za-zµμ]))"
)
ABSTRACT_HEADING = "摘要"
ABSTRACT_ENDINGS = ("关键词", "关键字")
EVALUATION_HEADINGS = ("模型的评价", "模型评价", "模型的优缺点", "模型优缺点")
EVALUATION_BOUNDARIES = ("参考文献", "附录", "AI 工具使用声明", "AI 声明", "AI声明")
REFERENCE_HEADING = "参考文献"
APPENDIX_HEADING = "附录"
# 附录起点标记。必须容忍排版引入的编号前缀：ctexart 的 \appendix 默认把标题排成
# 「A 支撑材料文件列表」，字面量 "附录 A" 与 "附录A" 都不命中，截断点会落到编号之后。
APPENDIX_MARKER_RE = re.compile(
    r"附\s*录\s*[A-Za-z]?(?:\s*[.、])?\s*(?=支|\S)"
    r"|(?:[A-Za-z]\s*[.、]?\s*)?支\s*撑\s*材\s*料\s*文\s*件\s*列\s*表"
)
# 截断点落在附录标题内部时，共享段会多带出标题**开头**的几个字符（如 ctexart 把
# \appendix 排成「A 支撑材料文件列表」，正则命中「支」而漏掉前面的「附录A」）。
# 这类偏移的尾巴只可能由附录标题自身的字符构成且极短；不加这条约束，任何追加到
# 提交版末尾的正文都会被当成「截断偏移」放行——那是把 SCIENTIFIC_BODY_DRIFT
# 这道门禁降级成 warning，实测 32 字结论句即可无声通过。
APPENDIX_TAIL_RE = re.compile(r"[附录支撑材料文件列表a-z0-9.、]{1,12}")
# 反编造的参考文献校验默认开启，库位置自锚到脚本旁；显式传参可覆盖。
DEFAULT_LITERATURE_LIBRARY = (
    Path(__file__).resolve().parent.parent / "references" / "literature-library.md"
)
# 参考文献条目的可解析标识。缺少全部三者的条目无法核验，等同于凭记忆书写。
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+")
ISBN_RE = re.compile(r"ISBN[\s:]*[\d\-Xx]{10,17}")
URL_RE = re.compile(r"https?://\S+")


def normalize(text: str) -> str:
    return re.sub(r"\s+", "", text).casefold()


def add_issue(target: list[dict[str, str]], code: str, message: str) -> None:
    target.append({"code": code, "message": message})


def read_csv(path: Path, expected: list[str]) -> tuple[list[dict[str, str]], str | None]:
    if not path.is_file():
        return [], f"文件不存在：{path}"
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != expected:
                return [], f"列应为 {expected}，实际为 {reader.fieldnames}"
            return [{key: (value or "").strip() for key, value in row.items()} for row in reader], None
    except (OSError, csv.Error, UnicodeError) as exc:
        return [], str(exc)


def read_document(path: Path) -> tuple[str, str | None]:
    if not path.is_file():
        return "", f"文件不存在：{path}"
    if path.suffix.lower() != ".pdf":
        try:
            return path.read_text(encoding="utf-8"), None
        except (OSError, UnicodeError) as exc:
            return "", str(exc)
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", str(path), "-"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return "", "未找到 pdftotext，无法回读 PDF"
    if result.returncode:
        return "", result.stderr.strip() or "pdftotext 回读失败"
    return result.stdout, None


def pdf_pages(path: Path) -> tuple[int | None, str | None]:
    if path.suffix.lower() != ".pdf" or not path.is_file():
        return None, None
    try:
        result = subprocess.run(
            ["pdfinfo", str(path)], capture_output=True, text=True, check=False
        )
    except FileNotFoundError:
        return None, "未找到 pdfinfo，页数未核验"
    if result.returncode:
        return None, result.stderr.strip() or "pdfinfo 回读失败"
    match = re.search(r"^Pages:\s*(\d+)\s*$", result.stdout, re.MULTILINE)
    return (int(match.group(1)), None) if match else (None, "pdfinfo 未返回页数")


def build_normalized_index(text: str) -> tuple[str, list[int]]:
    """返回去空白并 casefold 的文本，以及归一化下标到原文偏移的映射。"""
    chars: list[str] = []
    positions: list[int] = []
    for offset, char in enumerate(text):
        if not char.isspace():
            chars.append(char.casefold())
            positions.append(offset)
    return "".join(chars), positions


def find_raw_position(norm_text: str, positions: list[int], snippet: str) -> tuple[int, int] | None:
    needle = re.sub(r"\s+", "", snippet).casefold()
    if not needle:
        return None
    index = norm_text.find(needle)
    if index < 0:
        return None
    return positions[index], positions[index + len(needle) - 1] + 1


def find_all_raw_positions(norm_text: str, positions: list[int], snippet: str) -> list[tuple[int, int]]:
    needle = re.sub(r"\s+", "", snippet).casefold()
    found: list[tuple[int, int]] = []
    start = 0
    while needle:
        index = norm_text.find(needle, start)
        if index < 0:
            break
        found.append((positions[index], positions[index + len(needle) - 1] + 1))
        start = index + 1
    return found


def cjk_count(text: str) -> int:
    return len(CJK_RE.findall(text))


def count_numbered_equations(text: str) -> int:
    return sum(1 for line in text.splitlines() if EQUATION_NUMBER_RE.search(line))


def count_tables(text: str) -> int:
    return len(set(TABLE_LABEL_RE.findall(text)))


def count_figures(text: str) -> int:
    return len(set(FIGURE_LABEL_RE.findall(text)))


def count_references(reader_text: str, norm_text: str, positions: list[int]) -> tuple[int, bool]:
    heading = find_raw_position(norm_text, positions, REFERENCE_HEADING)
    if not heading:
        return len(REFERENCE_ENTRY_RE.findall(reader_text)), False
    end = len(reader_text)
    appendix = find_raw_position(norm_text, positions, APPENDIX_HEADING)
    if appendix and appendix[0] > heading[1]:
        end = appendix[0]
    return len(REFERENCE_ENTRY_RE.findall(reader_text[heading[1]:end])), True


def extract_reference_entries(reader_text: str, norm_text: str, positions: list[int]) -> list[str]:
    """按 [n] 切出参考文献区的逐条条目原文。"""
    heading = find_raw_position(norm_text, positions, REFERENCE_HEADING)
    start = heading[1] if heading else 0
    end = len(reader_text)
    appendix = find_raw_position(norm_text, positions, APPENDIX_HEADING)
    if appendix and appendix[0] > start:
        end = appendix[0]
    block = reader_text[start:end]
    marks = [match.start() for match in REFERENCE_ENTRY_RE.finditer(block)]
    if not marks:
        return []
    bounds = marks + [len(block)]
    return [block[bounds[i] : bounds[i + 1]].strip() for i in range(len(marks))]


def load_library_index(path: Path) -> tuple[set[str], set[str], str | None]:
    """从 literature-library.md 抽取可核验标识与题名。

    只认表格行：库的正文散文里也会出现 DOI 示例，把它们当条目会放行编造的引用。
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return set(), set(), f"文献库不可读：{exc}"
    identifiers: set[str] = set()
    titles: set[str] = set()
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        for cell in cells:
            identifiers.update(match.group(0).lower() for match in DOI_RE.finditer(cell))
            identifiers.update(
                re.sub(r"[^0-9Xx]", "", match.group(0)).lower() for match in ISBN_RE.finditer(cell)
            )
        for match in re.finditer(r"《([^》]+)》", line):
            titles.add(normalize(match.group(1)).lower())
        if len(cells) >= 2 and len(cells[1]) >= 12:
            titles.add(normalize(cells[1]).lower())
    if not identifiers and not titles:
        return identifiers, titles, "文献库未解析到任何条目（表格结构可能已变更）"
    return identifiers, titles, None


def validate_results_ledger(
    ledger_path: Path | None,
    reader_text: str,
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
) -> dict[str, object] | None:
    """核验 RESULTS.md 里每条 R-id 的数值确实进了论文。

    终检清单要求「摘要数字 = 正文数字 = 图表数字 = RESULTS.md」，此前全靠人工比对。
    这里做可证伪的那一半：台账登记了某个结果，论文里却一个对应数值都找不到，
    说明台账与论文已经脱节——要么论文漏报了这个结果，要么台账里是废弃记录没标状态。

    只取 ≥4 位小数的高精度数值作判据：整数和一两位小数在任何论文里都可能偶然出现，
    拿它们比对会产出大量假通过，比不查更糟。
    """
    if ledger_path is None:
        return None
    if not ledger_path.is_file():
        add_issue(warnings, "RESULTS_LEDGER_MISSING", f"结果台账不存在：{ledger_path}")
        return {"status": "SKIPPED", "checked": None, "absent": None}

    normalized_reader = normalize(reader_text).replace(".", "")
    rows = [
        line for line in ledger_path.read_text(encoding="utf-8").splitlines()
        if line.startswith("| R-")
    ]
    checked, absent, skipped = 0, [], 0
    for line in rows:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 11:
            continue
        rid, name, value, status = cells[0], cells[1], cells[2], cells[10]
        # 已被取代或作废的记录本就不该出现在论文里。
        if status.upper() in {"STALE", "SUPERSEDED"}:
            skipped += 1
            continue
        numbers = re.findall(r"\d+\.\d{4,}", value)
        if not numbers:
            skipped += 1
            continue
        checked += 1
        if all(number.replace(".", "") not in normalized_reader for number in numbers):
            absent.append({"id": rid, "name": name[:40], "values": numbers[:3]})
    if absent:
        add_issue(
            errors,
            "RESULTS_NOT_IN_PAPER",
            "以下 R-id 的数值在论文中完全找不到，台账与论文已脱节："
            + "; ".join(f"{item['id']} {item['name']} {item['values']}" for item in absent)
            + "。要么论文漏报该结果，要么台账里是废弃记录未标 STALE/SUPERSEDED",
        )
    return {
        "status": "CHECKED", "ledger_rows": len(rows), "checked": checked,
        "skipped": skipped, "absent": absent,
    }


def validate_pagination(
    path: Path,
    text: str,
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
) -> dict[str, object] | None:
    """核验页码自第 1 页起连续。

    规则第 42 条「摘要专用页（从此页起编页码）」+ 第 44 条「阿拉伯数字从 1 连续编号」。
    实测踩过的坑：LaTeX 模板在摘要后写了 \\setcounter{page}{1}，结果摘要标 1–2、
    正文又从 1 重新计，全文两套页码。终检清单里这一条此前全靠人眼翻页。

    判据只认每页最后一行且整行为纯数字的页脚——正文里的章节号、公式号、表号都可能
    是孤立数字，放宽判据会把它们当页码，产出大量假报。
    """
    if path.suffix.lower() != ".pdf" or not path.is_file():
        return None
    pages = text.split("\f")
    if pages and not pages[-1].strip():
        pages = pages[:-1]
    numbered: dict[int, int] = {}
    for index, page in enumerate(pages, start=1):
        lines = [line.strip() for line in page.splitlines() if line.strip()]
        if lines and re.fullmatch(r"\d{1,3}", lines[-1]):
            numbered[index] = int(lines[-1])
    if not numbered:
        add_issue(warnings, "PAGINATION_NOT_DETECTED", f"{path.name} 未识别到页脚页码，需人工核对")
        return {"status": "SKIPPED", "pages": len(pages), "numbered": None, "mismatched": None}
    mismatched = [
        {"pdf_page": index, "footer": value}
        for index, value in sorted(numbered.items())
        if value != index
    ]
    if mismatched:
        add_issue(
            errors,
            "PAGINATION_DISCONTINUOUS",
            f"{path.name} 页脚页码与 PDF 页序不一致（前几处：{mismatched[:4]}）。"
            "规则要求自摘要页起从 1 连续编号；常见原因是模板在摘要后重置了 page 计数器",
        )
    missing = [i for i in range(1, len(pages) + 1) if i not in numbered]
    if missing:
        add_issue(
            warnings,
            "PAGINATION_MISSING_ON_PAGES",
            f"{path.name} 第 {missing[:6]} 页未识别到页脚页码",
        )
    return {
        "status": "CHECKED", "pages": len(pages), "numbered": len(numbered),
        "mismatched": mismatched, "missing": missing[:10],
    }


def validate_references(
    entries: list[str],
    library_path: Path | None,
    citation_log: Path | None,
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
    library_explicit: bool = True,
) -> dict[str, object]:
    """核验每条参考文献是否可追溯。

    反幻觉铁律要防的正是「我记得这篇文献应该没错」：既不在库内、又没有任何
    可解析标识的条目，与凭记忆书写在证据上不可区分，因此判 error 而非 warning。

    未核验时各项计数一律置 None 而非 0：`"unsourced": 0` 与「真查了、零条未溯源」
    字面完全一样，是这份报告最容易骗过人眼的一处。

    `library_explicit` 区分库路径的来源——显式传入的路径读不到是**内容问题**（判 error），
    默认路径不存在只是脚本被单独拷走的**环境布局问题**（判 warning 并换 code），
    后者若一律判 error 会把一篇参考文献完全合规的论文判成 FAIL_CONTRACT。
    """
    summary: dict[str, object] = {
        "checked": len(entries),
        "library_hits": None,
        "identifier_only": None,
        "contest_sources": None,
        "unsourced": None,
    }
    if library_path is None:
        add_issue(errors, "REFERENCE_CHECK_SKIPPED", "未提供 --literature-library，参考文献可追溯性未核验")
        summary["status"] = "SKIPPED"
        return summary
    if not library_path.is_file():
        if library_explicit:
            add_issue(errors, "REFERENCE_LIBRARY_UNREADABLE", f"指定的书目库不存在：{library_path}")
            summary["status"] = "SKIPPED"
        else:
            add_issue(
                warnings,
                "REFERENCE_LIBRARY_DEFAULT_MISSING",
                f"默认书目库不在脚本旁（{library_path}），参考文献可追溯性未核验。"
                "脚本被单独拷贝时会出现这种情况，显式传 --literature-library 指定库位置",
            )
            summary["status"] = "SKIPPED"
        return summary
    identifiers, titles, library_error = load_library_index(library_path)
    if library_error:
        add_issue(errors, "REFERENCE_LIBRARY_UNREADABLE", library_error)
        summary["status"] = "SKIPPED"
        return summary

    # 走到这里才是真的开始核验，计数从 0 起算——上面的 None 表示「未核验」。
    summary.update(library_hits=0, identifier_only=0, contest_sources=0, unsourced=0)

    log_text = ""
    if citation_log is not None:
        try:
            log_text = citation_log.read_text(encoding="utf-8").lower()
        except OSError as exc:
            add_issue(warnings, "CITATION_LOG_UNREADABLE", f"实访记录不可读：{exc}")

    for entry in entries:
        label = entry[:60].replace("\n", " ")
        # pdftotext 会在版心边界折行，把 DOI 和 ISBN 从中间截断。不先规整就会把
        # 「著录规范、标识完整」的条目误判成「无法核验」——纪律不变，但判据必须
        # 作用在完整字符串上。
        compact = re.sub(r"[\s­‐-―]+", "", entry)
        normalized = normalize(entry).lower()
        # 句末标点会被 DOI/URL 的字符类吞掉（DOI 允许 '.'），比对时须剥离。
        entry_ids = [match.group(0).lower().rstrip(".,;:)]") for match in DOI_RE.finditer(compact)]
        entry_ids += [match.group(0).lower().rstrip(".,;:)]") for match in URL_RE.finditer(compact)]
        entry_isbns = [
            re.sub(r"[^0-9Xx]", "", match.group(0)).lower() for match in ISBN_RE.finditer(compact)
        ]
        hit_library = (
            any(identifier in entry_ids for identifier in identifiers if identifier)
            or any(identifier in entry_isbns for identifier in identifiers if identifier)
            or any(title in normalized for title in titles if title)
        )
        has_identifier = bool(entry_ids) or bool(entry_isbns)
        is_contest_source = any(
            token in entry for token in ("数学建模竞赛", "赛题", "官方附件", "题面", "组委会")
        )

        if hit_library:
            summary["library_hits"] = int(summary["library_hits"]) + 1
        elif is_contest_source:
            summary["contest_sources"] = int(summary["contest_sources"]) + 1
            add_issue(warnings, "CONTEST_SOURCE_REFERENCE", f"题面/官方来源条目，豁免库校验：{label}")
        elif has_identifier:
            summary["identifier_only"] = int(summary["identifier_only"]) + 1
            verified = bool(log_text) and any(entry_id in log_text for entry_id in entry_ids)
            if verified:
                add_issue(warnings, "REFERENCE_OUTSIDE_LIBRARY_VERIFIED", f"库外条目，已有实访记录：{label}")
            else:
                add_issue(
                    warnings,
                    "REFERENCE_NOT_IN_LIBRARY",
                    f"库外条目且无实访记录，MUST 实访 https://doi.org/<DOI> 后登记到 SOURCES.md：{label}",
                )
        else:
            summary["unsourced"] = int(summary["unsourced"]) + 1
            add_issue(
                errors,
                "REFERENCE_UNSOURCED",
                f"条目既不在 literature-library.md 内，也无 DOI/ISBN/URL 可核验：{label}",
            )
    summary["status"] = "CHECKED"
    return summary


def count_keywords(reader_text: str, norm_text: str, positions: list[int]) -> int | None:
    """数摘要末尾的关键词个数；定位失败返回 None，不猜。"""
    for marker in ABSTRACT_ENDINGS:
        span = find_raw_position(norm_text, positions, marker)
        if not span:
            continue
        tail = reader_text[span[1] : span[1] + 300]
        tail = tail.lstrip("：: \t")
        line = tail.split("\n\n")[0].splitlines()
        joined = " ".join(part.strip() for part in line[:2])
        parts = [part.strip() for part in re.split(r"[;；,，、]|\s{2,}", joined) if part.strip()]
        if parts:
            return len(parts)
    return None


def locate_abstract(reader_text: str, norm_text: str, positions: list[int]) -> dict[str, object]:
    result: dict[str, object] = {"located": False, "cjk_chars": None, "unit_values": None}
    keyword = None
    for marker in ABSTRACT_ENDINGS:
        keyword = find_raw_position(norm_text, positions, marker)
        if keyword:
            break
    if not keyword:
        return result
    headings = [span for span in find_all_raw_positions(norm_text, positions, ABSTRACT_HEADING) if span[1] <= keyword[0]]
    if not headings:
        return result
    abstract = reader_text[headings[-1][1] : keyword[0]]
    result.update(
        located=True,
        cjk_chars=cjk_count(abstract),
        unit_values=len(UNIT_VALUE_RE.findall(abstract)),
    )
    return result


def locate_evaluation(reader_text: str, norm_text: str, positions: list[int]) -> dict[str, object]:
    result: dict[str, object] = {"located": False, "cjk_chars": None, "start": None}
    reference = find_raw_position(norm_text, positions, REFERENCE_HEADING)
    limit = reference[0] if reference else len(reader_text)
    headings: list[tuple[int, int]] = []
    for marker in EVALUATION_HEADINGS:
        headings.extend(span for span in find_all_raw_positions(norm_text, positions, marker) if span[0] < limit)
    if not headings:
        return result
    start = max(span[0] for span in headings)
    end = limit
    for marker in EVALUATION_BOUNDARIES:
        boundary = find_raw_position(norm_text, positions, marker)
        if boundary and start < boundary[0] < end:
            end = boundary[0]
    result.update(located=True, cjk_chars=cjk_count(reader_text[start:end]), start=start)
    return result


def locate_question_spans(
    coverage_rows: list[dict[str, str]],
    reader_text: str,
    norm_text: str,
    positions: list[int],
    extra_boundaries: Iterable[int] = (),
) -> dict[str, dict[str, object]]:
    """用覆盖账本各行 paper_anchor 框定每问区间；定位失败的问只标记不伪造。"""
    questions: dict[str, dict[str, object]] = {}
    for row in coverage_rows:
        entry = questions.setdefault(
            row["question_id"], {"anchor_starts": [], "na_components": 0, "definition_na": False}
        )
        status = row["status"].upper()
        component = row["component"].lower()
        if status == "N_A":
            entry["na_components"] += 1
            if component == "definition":
                entry["definition_na"] = True
            continue
        if component in NON_NA_COMPONENTS and row["paper_anchor"]:
            found = find_raw_position(norm_text, positions, row["paper_anchor"])
            if found:
                entry["anchor_starts"].append(found[0])
    starts = {question: min(item["anchor_starts"]) for question, item in questions.items() if item["anchor_starts"]}
    ordered = sorted(starts, key=lambda question: starts[question])
    tail_boundaries = list(extra_boundaries)
    for marker in EVALUATION_BOUNDARIES:
        found = find_raw_position(norm_text, positions, marker)
        if found:
            tail_boundaries.append(found[0])
    spans: dict[str, tuple[int, int]] = {}
    for index, question in enumerate(ordered):
        start = starts[question]
        if index + 1 < len(ordered):
            end = starts[ordered[index + 1]]
        else:
            end = min((boundary for boundary in tail_boundaries if boundary > start), default=len(reader_text))
        spans[question] = (start, end)
    metrics: dict[str, dict[str, object]] = {}
    for question, entry in questions.items():
        span = spans.get(question)
        item: dict[str, object] = {
            "span_available": span is not None,
            "na_components": entry["na_components"],
            "prose_floor_exempt": entry["na_components"] > 2,
            "equation_floor_exempt": bool(entry["definition_na"]),
            "cjk_chars": None,
            "numbered_equations": None,
        }
        if span is not None:
            segment = reader_text[span[0] : span[1]]
            item["cjk_chars"] = cjk_count(segment)
            item["numbered_equations"] = count_numbered_equations(segment)
        metrics[question] = item
    return metrics


def validate_coverage(
    rows: list[dict[str, str]], reader_text: str, errors: list[dict[str, str]], expansions: list[dict[str, str]]
) -> str:
    by_question: dict[str, list[dict[str, str]]] = {}
    human_states: set[str] = set()
    reader_normalized = normalize(reader_text)
    for index, row in enumerate(rows, start=2):
        question = row["question_id"]
        component = row["component"].lower()
        if not question:
            add_issue(errors, "EMPTY_QUESTION_ID", f"覆盖账本第 {index} 行缺 question_id")
            continue
        by_question.setdefault(question, []).append(row)
        if component not in COMPONENTS:
            add_issue(errors, "UNKNOWN_COMPONENT", f"{question} 使用未知 component={component}")
            continue
        if not row["required_content"] or not row["observed"]:
            add_issue(expansions, "EMPTY_COVERAGE_OBSERVATION", f"{question}/{component} 缺 required_content 或 observed")
        status = row["status"].upper()
        if status in {"WEAK", "MISSING"}:
            add_issue(expansions, f"COVERAGE_{status}", f"{question}/{component}={status}")
        elif status == "N_A":
            if component in NON_NA_COMPONENTS:
                add_issue(errors, "ILLEGAL_N_A", f"{question}/{component} 不允许 N_A")
            if not DECISION_ID_RE.search(row["evidence_ids"] + " " + row["observed"]):
                add_issue(errors, "N_A_WITHOUT_DECISION", f"{question}/{component} 的 N_A 缺 D-id 与理由")
        elif status != "PASS":
            add_issue(errors, "INVALID_COVERAGE_STATUS", f"{question}/{component} 使用 status={status or '<empty>'}")
        anchor = row["paper_anchor"]
        if status != "N_A":
            normalized_anchor = normalize(anchor) if anchor else ""
            hits = reader_normalized.count(normalized_anchor) if anchor else 0
            if hits == 0 and normalized_anchor and \
                    found_allowing_page_number(normalized_anchor, reader_normalized):
                hits = 1        # 被行号或页码打断，不是真的找不到
            if hits == 0:
                add_issue(errors, "ANCHOR_NOT_FOUND",
                          f"{question}/{component} 的 paper_anchor 无法在阅读版检索：{anchor or '<empty>'}")
            elif hits > 1:
                # 锚点用于切出每问的正文区间。全文出现多次时区间会串到别章，
                # 后续的每问字数、公式数、图表数统统算到错误的章节上，而报告看起来完全正常。
                # 2025C 实测：「任务接口」「解释边界」在四章都有，Q1 被算成 11 个编号公式
                # （实有 3 个）、Q2 被算成 0 个（实有 8 个）。此前只查「找得到」，
                # 于是这类锚点一路放行。锚点必须唯一，且不含数学符号（PDF 回读的是渲染后文本）。
                add_issue(errors, "ANCHOR_NOT_UNIQUE",
                          f"{question}/{component} 的 paper_anchor 在阅读版出现 {hits} 次，"
                          f"无法唯一定位区间：{anchor}。改用该问独有的短语——"
                          "非唯一锚点会把每问区间串到别章，使逐问统计静默算错。")
        if component == "validation":
            if not RISK_ID_RE.search(row["claim_or_risk_ids"]):
                add_issue(errors, "VALIDATION_WITHOUT_RISK", f"{question}/validation 未关联 K-id")
            if status != "N_A" and not VALIDATION_ID_RE.search(row["evidence_ids"]):
                add_issue(errors, "VALIDATION_WITHOUT_EVIDENCE", f"{question}/validation 未关联 R/P-id")
        if component == "result" and not VALIDATION_ID_RE.search(row["evidence_ids"]):
            add_issue(errors, "RESULT_WITHOUT_EVIDENCE", f"{question}/result 未关联 R/P-id")
        if component in {"definition", "algorithm"} and not ID_RE.search(row["claim_or_risk_ids"]):
            add_issue(errors, "MODEL_ELEMENT_WITHOUT_CLAIM", f"{question}/{component} 未关联 C/K-id")
        human = row["human_status"].upper()
        if human not in {"PENDING", "PROXY_REHEARSAL", "HUMAN_ACCEPTED"}:
            add_issue(errors, "INVALID_HUMAN_STATUS", f"{question}/{component} 使用 human_status={human or '<empty>'}")
        else:
            human_states.add(human)

    if not by_question:
        add_issue(errors, "EMPTY_COVERAGE_LEDGER", "覆盖账本没有数据行")
    for question, question_rows in by_question.items():
        found = [row["component"].lower() for row in question_rows]
        missing = COMPONENTS - set(found)
        duplicates = sorted({item for item in found if found.count(item) > 1})
        if missing:
            add_issue(errors, "MISSING_COMPONENT", f"{question} 缺 {sorted(missing)}")
        if duplicates:
            add_issue(errors, "DUPLICATE_COMPONENT", f"{question} 重复 {duplicates}")

    if human_states == {"HUMAN_ACCEPTED"}:
        return "HUMAN_ACCEPTED"
    if human_states == {"PROXY_REHEARSAL"}:
        return "PROXY_REHEARSAL"
    return "PENDING"


def validate_rubric(
    rows: list[dict[str, str]], target_score: float, errors: list[dict[str, str]], expansions: list[dict[str, str]]
) -> float:
    seen: set[str] = set()
    total = 0.0
    for index, row in enumerate(rows, start=2):
        dimension = row["dimension"]
        if dimension not in RUBRIC:
            add_issue(errors, "UNKNOWN_RUBRIC_DIMENSION", f"rubric 第 {index} 行未知维度：{dimension}")
            continue
        if dimension in seen:
            add_issue(errors, "DUPLICATE_RUBRIC_DIMENSION", f"rubric 重复维度：{dimension}")
            continue
        seen.add(dimension)
        expected_max, expected_pass = RUBRIC[dimension]
        try:
            score = float(row["score"])
            maximum = float(row["max_score"])
            pass_score = float(row["pass_score"])
        except ValueError:
            add_issue(errors, "INVALID_RUBRIC_NUMBER", f"{dimension} 分值不是数字")
            continue
        if maximum != expected_max or pass_score != expected_pass:
            add_issue(errors, "RUBRIC_SCALE_DRIFT", f"{dimension} 应为满分/及格 {expected_max}/{expected_pass}")
        if not 0 <= score <= expected_max:
            add_issue(errors, "RUBRIC_SCORE_OUT_OF_RANGE", f"{dimension} score={score}")
        if not row["evidence"] or not row["observed"]:
            add_issue(errors, "RUBRIC_WITHOUT_EVIDENCE", f"{dimension} 缺 evidence 或 observed")
        expected_status = "PASS" if score >= expected_pass else "FAIL"
        if row["status"].upper() != expected_status:
            add_issue(errors, "RUBRIC_STATUS_MISMATCH", f"{dimension} 应标 {expected_status}")
        if score < expected_pass:
            add_issue(expansions, "RUBRIC_ITEM_BELOW_PASS", f"{dimension} {score} < {expected_pass}")
        total += score
    missing = set(RUBRIC) - seen
    if missing:
        add_issue(errors, "MISSING_RUBRIC_DIMENSION", f"rubric 缺 {sorted(missing)}")
    if total < target_score:
        add_issue(expansions, "RUBRIC_BELOW_TARGET", f"总分 {total:g} < 目标 {target_score:g}")
    return total


def found_allowing_page_number(anchor: str, haystack: str, max_digits: int = 5) -> bool:
    """锚点在 haystack 中出现，允许中间被至多一处纯数字打断。

    PDF 回读的是渲染后的文本流，其中混着行号与页码。它们会插进句子或代码行的中间：
    实测两例——`"status")33]`（lstlisting 行号 33 卡在 `)` 与 `]` 之间）、
    `这不是模型失效而6是地形使然`（页码 6 卡在句子中间）。两次都报成了假的
    ANCHOR_NOT_FOUND / APPENDIX_CODE_STALE。

    只在直接匹配失败后才调用本函数，且只允许**一处**插入：允许多处会让匹配过于宽松，
    把真正的内容差异也放过去。切分点自适应采样，短锚点逐字符试、长锚点按比例抽样，
    上限约 16 次；写死步长 4 会让 6 字符的短锚点一个切分点都取不到（本轮踩过）。
    """
    if anchor in haystack:
        return True
    step = max(1, len(anchor) // 16)
    for cut in range(1, len(anchor), step):
        head, tail = anchor[:cut], anchor[cut:]
        if re.search(re.escape(head) + r"\d{1,%d}" % max_digits + re.escape(tail), haystack):
            return True
    return False


def source_signature(path: Path) -> str | None:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return None
    candidates = [
        line.strip()
        for line in lines
        if 12 <= len(line.strip()) <= 160 and not line.lstrip().startswith(("#", "//", "%"))
    ]
    return max(candidates, key=len, default=None)


# 逐问篇幅的最大/最小比值上限，超过即提示失衡。依据见 assess_targets 内注释。
QUESTION_BALANCE_RATIO = 3.0
ANCHOR_MIN_LEN = 16
# 原始行（含缩进）超过此长度就不做锚点。lstlisting 的 breaklines 会在显示宽度处
# 折断长行，而续行照样带行号，于是行号数字被插进代码中间——2025D 实测：
# 一行 103 字符的源码在 PDF 里变成 `"status")33]`，行号 33 卡在 `)` 与 `]` 之间，
# 报出 133 条锚点缺 1 条的假漂移。「行内片段不会被行号打断」这个前提，
# 只在行不被折断时成立。
ANCHOR_MAX_RAW_LEN = 90
# 命中率低于此值判定为「根本没收录」，而不是「收录了但过期」。
# 依据（2025C 实测三组）：版本一致 100%；版本过期（nipt_core.py 少了路径自锚定那几行）
# 84.6%；根本没收录（build_paper.py 不在附录里）10%——后者的命中全部来自
# `import subprocess` 这类通用行在别的文件中的偶然匹配。三组间距很宽，取 50% 居中。
EMBEDDED_HIT_RATE = 0.5


def source_anchors(path: Path, min_len: int = ANCHOR_MIN_LEN) -> list[str]:
    """把源文件切成可在 PDF 里逐条回读的**行内**锚点，用于判定附录印的是不是当前版本。

    为什么必须是行内片段而不是跨行滑窗：附录用 lstlisting 排版且 `numbers=left`，
    行号数字会插在每行开头，跨行片段一定被打断；行内片段则不会——`breaklines` 折断
    长行只插入空白，`normalize()` 去空白后仍连续。只取纯 ASCII 行，避开中文注释在
    PDF 提取中的编码不确定性。

    为什么不是「抽一行签名」：`source_signature()` 只取最长的一行，那一行没改动时，
    附录里印的即使是整份旧代码也照样通过。2025C 实测正是这样漏掉的——修完
    nipt_core.py 的路径逃逸后重打了支撑包却没重编论文，交付版附录印的仍是修复前、
    跑不通的旧代码，而 code_check 比的是「支撑包 vs 工作区」，两边都是新版，全绿放行。
    这同时踩中格式规范第五条（附录源程序须完整可运行）与第十一条（支撑材料须与论文相符）。

    阈值依据（实测而非估计）：2025C 四个源文件 × min_len 12/16/24 共 12 组，
    版本一致时命中率全部为 100.00%，提取噪声底为 0；版本不一致时缺失的恰是改动过的
    那几行。故判据取「任何缺失都是真差异」，不设容错比例。
    """
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return []
    anchors: list[str] = []
    for line in lines:
        if not line.isascii() or len(line) > ANCHOR_MAX_RAW_LEN:
            continue
        squashed = normalize(line)
        if len(squashed) >= min_len:
            anchors.append(squashed)
    return anchors


def visible_files(root: Path) -> Iterable[Path]:
    if not root.is_dir():
        return []
    return (
        path
        for path in sorted(root.rglob("*"))
        if path.is_file()
        and not any(part.startswith(".") or part == "__pycache__" for part in path.relative_to(root).parts)
        and path.suffix.lower() != ".pyc"
    )


def validate_editions(
    reader_text: str,
    submission_text: str,
    source_root: Path | None,
    source_exclude: list[str] | None,
    support_root: Path | None,
    appendix_required: bool,
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
) -> None:
    if appendix_required:
        positions = [match.start() for match in APPENDIX_MARKER_RE.finditer(submission_text)]
    else:
        positions = []
    if appendix_required and not positions:
        add_issue(errors, "MISSING_FILE_LIST", "提交版缺‘附录 A 支撑材料文件列表’")
        shared_submission = submission_text
    elif positions:
        shared_submission = submission_text[: min(positions)]
    else:
        shared_submission = submission_text
    normalized_reader = normalize(reader_text)
    normalized_shared = normalize(shared_submission)
    if normalized_reader != normalized_shared:
        similarity = SequenceMatcher(
            None, normalized_reader, normalized_shared, autojunk=False
        ).ratio()
        if Counter(normalized_reader) == Counter(normalized_shared) and similarity >= 0.995:
            add_issue(
                warnings,
                "PDF_TEXT_ORDER_VARIANCE",
                f"两版字符集合一致且文本相似度 {similarity:.6f}；判为 PDF 公式提取顺序差异，仍须保留同源正文哈希",
            )
        elif (
            similarity >= 0.995
            and normalized_shared[: len(normalized_reader)] == normalized_reader
            and APPENDIX_TAIL_RE.fullmatch(normalized_shared[len(normalized_reader):])
        ):
            # 截断点落在附录标题内部时，shared 会多带几个编号字符（如 ctexart 把
            # \appendix 排成「A 支撑材料文件列表」）。正文本身逐字相同，差额只在尾部、
            # 长度可忽略、且**全部由附录标题字符构成**，才判为截断位置偏移而非正文漂移
            # ——否则报错会指向完全错误的原因。尾部一旦出现附录标题以外的字，说明提交版
            # 真的比阅读版多了内容，必须落到下面的 SCIENTIFIC_BODY_DRIFT。
            add_issue(
                warnings,
                "APPENDIX_MARKER_OFFSET",
                f"共享正文为阅读版的前缀，尾部多出 {len(normalized_shared) - len(normalized_reader)} 字符"
                f"（{normalized_shared[len(normalized_reader):][:12]!r}）；判为附录标题截断位置偏移，正文同源",
            )
        else:
            add_issue(
                errors,
                "SCIENTIFIC_BODY_DRIFT",
                f"阅读版与提交版的共享科学正文不一致（相似度 {similarity:.6f}；"
                f"阅读版 {len(normalized_reader)} 字符 / 共享段 {len(normalized_shared)} 字符）。"
                "相似度接近 1 时优先检查附录标题排版是否使截断点偏移，而非正文内容差异",
            )
    if not appendix_required:
        return
    if "源程序" not in submission_text:
        add_issue(errors, "MISSING_SOURCE_APPENDIX", "提交版缺完整源程序附录")
    normalized_submission = normalize(submission_text)
    if support_root is not None:
        if not support_root.is_dir():
            # 路径落空 ≠ 只少一项检查：其下的逐文件列表核对整组不会执行。
            # 实测后果——2025A 演练因交付物未分层而传了不存在的 staging 路径，
            # 报告只显示这一条 error，被读成「支撑包已通过终检」，而实际有一个
            # 论文完全没提到的文件从未被发现。
            add_issue(
                errors,
                "MISSING_SUPPORT_ROOT",
                f"支撑目录不存在：{support_root}。**其下逐文件列表核对整组未执行**——"
                "本次报告不构成支撑材料完整性的任何证据，先修路径再重跑",
            )
        else:
            for path in visible_files(support_root):
                relative = path.relative_to(support_root).as_posix()
                # 目录级声明覆盖其下文件：附录里写一行 `figures/` 即代表整个目录，
                # 无须把每张图的同名 .csv 逐个列进论文。逐文件比对会逼人把几十个
                # 文件名塞进正文（既不合国赛论文惯例，又挤占篇幅），或者永远 FAIL——
                # 那不是让人写清楚，是让人二选一地作弊。
                # 顶层散落文件仍须具名：它们没有可声明的父目录。
                ancestors = [
                    f"{parent.as_posix()}/"
                    for parent in Path(relative).parents
                    if parent.as_posix() not in (".", "")
                ]
                if normalize(relative) in normalized_submission:
                    continue
                if any(normalize(ancestor) in normalized_submission for ancestor in ancestors):
                    continue
                add_issue(errors, "SUPPORT_FILE_NOT_LISTED", f"提交版文件列表未找到：{relative}")
    if source_root is not None:
        if not source_root.is_dir():
            add_issue(
                errors,
                "MISSING_SOURCE_ROOT",
                f"源程序目录不存在：{source_root}。**源码具名与代码嵌入核对整组未执行**——"
                "规则要求提交版附录含完整源程序，这一项当前无任何证据",
            )
        else:
            code_files = [path for path in visible_files(source_root) if path.suffix.lower() in CODE_SUFFIXES]
            # 权威源码目录里通常混着不进附录的工具脚本（排版、绘图、下载）。
            # 规范只要求附录含「建模用到的」源程序，把这些排掉不是放松检查——
            # 相反，正因为能排掉它们，--source-root 才敢指向权威源码目录而不是支撑包副本，
            # 而只有指向权威源码，APPENDIX_CODE_STALE 才检得出「改了代码没重编论文」。
            excluded: list[str] = []
            if source_exclude:
                kept = []
                for path in code_files:
                    relative = path.relative_to(source_root).as_posix()
                    if any(fnmatch.fnmatch(relative, pattern) or
                           fnmatch.fnmatch(path.name, pattern) for pattern in source_exclude):
                        excluded.append(relative)
                    else:
                        kept.append(path)
                code_files = kept
                if excluded:
                    add_issue(
                        warnings, "SOURCE_FILES_EXCLUDED",
                        "按 --source-exclude 跳过、未做附录核对的源文件："
                        + "、".join(sorted(excluded))
                        + "。它们因此不受「附录须含完整可运行源程序」这一项保护，"
                          "排除理由须能说明它们确实不属于建模程序。",
                    )
            if not code_files:
                add_issue(errors, "NO_SOURCE_FILES", f"源程序目录没有可识别代码：{source_root}")
            for path in code_files:
                relative = path.relative_to(source_root).as_posix()
                # 具名与内容分两个独立维度判定。原先「文件名没出现就 continue」会在
                # 最该深查的情形下反而跳过内容核对，等于放弃了更强的判据。
                named = (
                    normalize(relative) in normalized_submission
                    or normalize(path.name) in normalized_submission
                )
                anchors = source_anchors(path)
                missing = (
                    [anchor for anchor in anchors if anchor not in normalized_submission]
                    if anchors else None      # None = 无从核对，区别于「核对通过」的空列表
                )

                # --- 内容维度 ---
                if missing is None:
                    add_issue(
                        warnings,
                        "SOURCE_CONTENT_NOT_CHECKABLE",
                        f"{relative} 没有可回读的行内锚点（空文件或整份非 ASCII），"
                        "本次未对其做附录内容核对",
                    )
                elif (hit_rate := 1 - len(missing) / len(anchors)) < EMBEDDED_HIT_RATE:
                    # 命中率极低 = 根本没收录。少量命中来自 `import subprocess` 这类
                    # 通用行在别的文件里的偶然匹配，不能据此说成「版本过期」——
                    # 两者修法不同：一个要补 \lstinputlisting，一个要重编 PDF。
                    add_issue(
                        errors,
                        "SOURCE_CONTENT_NOT_EMBEDDED",
                        f"提交版未回读到 {relative} 的代码内容"
                        f"（{len(anchors)} 条行内锚点仅命中 {len(anchors) - len(missing)} 条，"
                        f"{hit_rate:.0%}，低于 {EMBEDDED_HIT_RATE:.0%} 即判定为未收录）。"
                        "若该文件本就不该进附录（如纯排版脚本），应把它移出 --source-root 的范围。",
                    )
                elif missing:
                    sample = "；".join(m[:60] for m in missing[:3])
                    add_issue(
                        errors,
                        "APPENDIX_CODE_STALE",
                        f"提交版附录里的 {relative} 不是当前版本："
                        f"{len(anchors)} 条行内锚点缺 {len(missing)} 条（命中 {hit_rate:.0%}），"
                        f"例如 {sample}。通常是改了源码却没重编论文 PDF——"
                        "附录印的代码与支撑包发出去的不是同一份，触发格式规范第五条与第十一条。"
                        "修法：重跑 build_paper.py 后重新生成交付物。",
                    )

                # --- 具名维度 ---
                if not named:
                    if missing == []:
                        # 代码逐行都回读到了，只是没在文件列表/小节标题里单独具名。
                        # 实测触发场景：附录标题写成「src/p1.py … src/p4.py（各问入口）」，
                        # 于是 p3.py 这个串全文没出现，但它的源码明明白白印在附录里。
                        # 这不构成取消资格风险，报 error 属误报；但文件列表该补，故留 warning。
                        add_issue(
                            warnings,
                            "SOURCE_FILE_NOT_NAMED",
                            f"提交版未单独出现源文件名 {relative}，但其代码已逐行回读到；"
                            "建议在支撑材料文件列表中逐个具名，避免评委按文件名核对时对不上",
                        )
                    else:
                        add_issue(
                            errors,
                            "SOURCE_FILE_NOT_NAMED",
                            f"提交版未出现源文件名：{relative}",
                        )


def assess_depth(
    reader_text: str,
    reader_pages: int | None,
    coverage_rows: list[dict[str, str]] | None,
    args: argparse.Namespace,
    expansions: list[dict[str, str]],
    warnings: list[dict[str, str]],
) -> dict[str, object]:
    """度量阅读版深度形态并执行 SPEC 门槛机检；触线才查形态项，定位失败只降级不伪造通过。"""
    norm_text, positions = build_normalized_index(reader_text)
    body_cjk = cjk_count(reader_text)
    abstract = locate_abstract(reader_text, norm_text, positions)
    evaluation = locate_evaluation(reader_text, norm_text, positions)
    body_tables = count_tables(reader_text)
    references, references_located = count_references(reader_text, norm_text, positions)
    question_metrics = (
        locate_question_spans(
            coverage_rows,
            reader_text,
            norm_text,
            positions,
            extra_boundaries=[evaluation["start"]] if evaluation["located"] else [],
        )
        if coverage_rows
        else {}
    )

    blocked: list[str] = []
    # 摘要与评价的形态项在触线之外无条件检查，但它们同样属于"深度形态核查"。
    # 不计入 form_failed 会让报告同时出现 ABSTRACT_DENSITY 与 DEPTH_FORM_CHECKS_PASSED
    # ——一边说摘要不达标，一边宣布形态全过并据此机检豁免。
    form_failed = False
    if abstract["located"]:
        if (
            abstract["cjk_chars"] < args.min_abstract_chars
            or abstract["unit_values"] < args.min_abstract_numbered_values
        ):
            form_failed = True
            add_issue(
                expansions,
                "ABSTRACT_DENSITY",
                f"摘要汉字 {abstract['cjk_chars']} / 含单位数值 {abstract['unit_values']} 处，"
                f"低于下限 {args.min_abstract_chars} 字 / {args.min_abstract_numbered_values} 处",
            )
    else:
        blocked.append("摘要")
        add_issue(warnings, "SPAN_UNAVAILABLE", "摘要区间定位失败（缺‘摘要/关键词’标记）；摘要密度退回人工核查，不伪造机检通过")
    if evaluation["located"]:
        if evaluation["cjk_chars"] < args.min_evaluation_chars:
            form_failed = True
            add_issue(expansions, "EVALUATION_FLOOR", f"模型评价汉字 {evaluation['cjk_chars']} < 下限 {args.min_evaluation_chars}")
    else:
        blocked.append("模型评价")
        add_issue(warnings, "SPAN_UNAVAILABLE", "模型评价区间定位失败；评价篇幅退回人工核查，不伪造机检通过")

    trigger_reasons: list[str] = []
    if reader_pages is not None and reader_pages < args.depth_trigger_pages:
        trigger_reasons.append(f"阅读版 {reader_pages} 页 < 触发线 {args.depth_trigger_pages} 页")
    if body_cjk < args.depth_trigger_chars:
        trigger_reasons.append(f"正文汉字 {body_cjk} < 触发线 {args.depth_trigger_chars}")
    triggered = bool(trigger_reasons)

    if triggered:
        if not coverage_rows:
            unavailable = ["<覆盖账本不可用>"]
        else:
            unavailable = [
                question
                for question, item in question_metrics.items()
                if not item["span_available"] and not (item["prose_floor_exempt"] and item["equation_floor_exempt"])
            ]
        if unavailable:
            blocked.append("每问区间")
            add_issue(
                warnings,
                "SPAN_UNAVAILABLE",
                f"{', '.join(unavailable)} 区间无法由覆盖账本 paper_anchor 定位；退回全量检查与人工核查，不伪造机检通过",
            )
        for question, item in question_metrics.items():
            if not item["span_available"]:
                continue
            if not item["prose_floor_exempt"] and item["cjk_chars"] < args.min_question_chars:
                form_failed = True
                add_issue(
                    expansions,
                    "QUESTION_PROSE_FLOOR",
                    f"{question} 建模求解区间汉字 {item['cjk_chars']} < 下限 {args.min_question_chars}",
                )
            if not item["equation_floor_exempt"] and item["numbered_equations"] < args.min_question_equations:
                form_failed = True
                add_issue(
                    expansions,
                    "QUESTION_EQUATION_FLOOR",
                    f"{question} 区间编号公式 {item['numbered_equations']} < 下限 {args.min_question_equations}",
                )
        if body_tables < args.min_body_tables:
            form_failed = True
            add_issue(expansions, "RESULT_TABLE_FLOOR", f"全文表格 {body_tables} 张 < 下限 {args.min_body_tables}")
        if references < args.min_references:
            form_failed = True
            add_issue(expansions, "REFERENCE_FLOOR", f"参考文献 {references} 条 < 下限 {args.min_references}")
        pages_desc = f"{reader_pages} 页" if reader_pages is not None else "页数未知"
        if not form_failed and not blocked:
            add_issue(
                warnings,
                "DEPTH_FORM_CHECKS_PASSED",
                f"触线（阅读版 {pages_desc} / 正文汉字 {body_cjk}）但深度形态核查全过；机检豁免留痕，H-004 仍须人工阅读 main.pdf 复核表达层",
            )
            add_issue(warnings, "DEPTH_REVIEW_REQUIRED", "触线但深度形态核查全过；页数不单独判失败，豁免以 DEPTH_FORM_CHECKS_PASSED 为准")
        elif form_failed:
            add_issue(
                warnings,
                "DEPTH_REVIEW_REQUIRED",
                f"触线（阅读版 {pages_desc} / 正文汉字 {body_cjk}）且深度形态核查存在缺项，详见 expansion_items；页数不单独判失败",
            )
        else:
            add_issue(
                warnings,
                "DEPTH_REVIEW_REQUIRED",
                f"触线（阅读版 {pages_desc} / 正文汉字 {body_cjk}）但部分深度形态项定位失败（SPAN_UNAVAILABLE），须人工核查；页数不单独判失败",
            )

    return {
        "reader_pages": reader_pages,
        "body_cjk_chars": body_cjk,
        "depth_triggered": triggered,
        "trigger_reasons": trigger_reasons,
        "questions": question_metrics,
        "body_tables": body_tables,
        "references": references,
        "references_located": references_located,
        "abstract": abstract,
        "evaluation": evaluation,
        "depth_form_checks_passed": triggered and not form_failed and not blocked,
        "thresholds": {
            "depth_trigger_pages": args.depth_trigger_pages,
            "depth_trigger_chars": args.depth_trigger_chars,
            "min_question_chars": args.min_question_chars,
            "min_question_equations": args.min_question_equations,
            "min_body_tables": args.min_body_tables,
            "min_abstract_chars": args.min_abstract_chars,
            "min_abstract_numbered_values": args.min_abstract_numbered_values,
            "min_evaluation_chars": args.min_evaluation_chars,
            "min_references": args.min_references,
        },
    }


def assess_targets(
    depth: dict[str, object],
    keywords: int | None,
    figures: int,
    warnings: list[dict[str, str]],
) -> dict[str, object]:
    """核查 rubric-and-writing.md §四的写作目标（target），与机检下限（floor）分开计。

    floor 只在触线时检查、判 NEEDS_EXPANSION；target 无条件检查、只出 warning。
    两者混为一谈是已实测的失效模式：本次演练 floor 全过而 target 8 项中 4 项、
    逐问 3/5 未达标，契约却报零 error，容易被读成「论文已达国一水平」。
    target 未达不阻断交付，但 MUST 留痕，让 H-004 知道差在哪。
    """
    gaps: list[dict[str, str]] = []

    def record(code: str, message: str) -> None:
        gaps.append({"code": code, "message": message})
        add_issue(warnings, code, message)

    def check_range(code: str, name: str, value: object, low: int, high: int | None, unit: str) -> None:
        if value is None:
            return
        number = int(value)
        if number < low:
            record(code, f"{name} {number}{unit} < 写作目标下限 {low}{unit}")
        elif high is not None and number > high:
            record(code, f"{name} {number}{unit} > 写作目标上限 {high}{unit}")

    pages = depth.get("reader_pages")
    check_range("TARGET_READER_PAGES", "阅读版页数", pages, 19, 29, " 页")
    check_range("TARGET_BODY_CHARS", "正文汉字", depth.get("body_cjk_chars"), 15000, None, " 字")
    check_range("TARGET_BODY_TABLES", "全文三线表", depth.get("body_tables"), 4, None, " 张")
    check_range("TARGET_BODY_FIGURES", "全文图", figures, 4, None, " 张")
    check_range("TARGET_REFERENCES", "参考文献", depth.get("references"), 3, 8, " 条")

    abstract = depth.get("abstract") or {}
    if abstract.get("located"):
        check_range("TARGET_ABSTRACT_CHARS", "摘要汉字", abstract.get("cjk_chars"), 600, 850, " 字")
        check_range("TARGET_ABSTRACT_VALUES", "摘要含单位数值", abstract.get("unit_values"), 8, None, " 处")
    if keywords is None:
        add_issue(warnings, "KEYWORD_COUNT_UNAVAILABLE", "关键词个数定位失败，退回人工核查")
    else:
        check_range("TARGET_KEYWORDS", "关键词", keywords, 4, 5, " 个")

    evaluation = depth.get("evaluation") or {}
    if evaluation.get("located"):
        check_range("TARGET_EVALUATION_CHARS", "模型评价汉字", evaluation.get("cjk_chars"), 230, 450, " 字")

    questions = depth.get("questions") or {}
    for question, item in questions.items():
        if not item.get("span_available"):
            continue
        if not item.get("prose_floor_exempt"):
            check_range(
                "TARGET_QUESTION_PROSE", f"{question} 建模求解汉字", item.get("cjk_chars"), 1200, None, " 字"
            )
        if not item.get("equation_floor_exempt"):
            check_range(
                "TARGET_QUESTION_EQUATIONS",
                f"{question} 编号公式",
                item.get("numbered_equations"),
                4,
                None,
                " 式",
            )

    # 问间均衡：只查每问的绝对下限，会漏掉「某问写透、某问一笔带过」这种失衡。
    # 评委按问分配注意力，最薄的一问决定观感；而过厚的一问往往是把不属于它的内容
    # 堆了进去。实测两例：2025C 四问 1659/1939/2000/3373 字（比值 2.03，观感均衡、
    # 契约零 error）；2025D 四问 1845/1191/778/2399（比值 3.08，Q3 一笔带过而 Q4
    # 承担了本该分给 Q3 的双源论述）。阈值 3.0 落在两者之间，且只作 warning——
    # 问间篇幅本就允许差异，只有悬殊到某问被架空才值得提醒。
    spans = {q: it.get("cjk_chars") for q, it in questions.items()
             if it.get("span_available") and it.get("cjk_chars")}
    if len(spans) >= 2:
        thinnest = min(spans, key=spans.get)
        thickest = max(spans, key=spans.get)
        ratio = spans[thickest] / spans[thinnest]
        if ratio > QUESTION_BALANCE_RATIO:
            record(
                "QUESTION_LENGTH_IMBALANCE",
                f"逐问篇幅悬殊：{thickest} {spans[thickest]} 字是 {thinnest} "
                f"{spans[thinnest]} 字的 {ratio:.2f} 倍（阈值 {QUESTION_BALANCE_RATIO}）。"
                f"最薄的一问决定评委观感；过厚的一问常是把本属别问的论述堆了进去。"
                f"检查 {thinnest} 是否被一笔带过，以及 {thickest} 里有没有该挪走的内容",
            )

    return {
        "status": "CHECKED",
        "gap_count": len(gaps),
        "gaps": gaps,
        "keywords": keywords,
        "figures": figures,
        "targets": {
            "reader_pages": "19-29",
            "body_cjk_chars": ">=15000",
            "question_cjk_chars": ">=1200",
            "question_equations": ">=4",
            "body_tables": ">=4",
            "body_figures": ">=4",
            "abstract_cjk_chars": "600-850",
            "abstract_unit_values": ">=8",
            "keywords": "4-5",
            "evaluation_cjk_chars": "230-450",
            "references": "3-8",
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coverage", type=Path, required=True)
    parser.add_argument("--rubric", type=Path, required=True)
    parser.add_argument("--reader", type=Path, required=True)
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--source-exclude", action="append", default=[],
                        help="不参与附录核对的源文件（glob，可多次）；用于排除排版、绘图这类非建模脚本")
    parser.add_argument("--support-root", type=Path)
    parser.add_argument("--target-score", type=float, default=88)
    parser.add_argument("--advisory-min-pages", type=int, default=18, help="已废弃：深度触线改由 --depth-trigger-pages/--depth-trigger-chars 控制")
    parser.add_argument("--max-body-pages", type=int, default=30)
    parser.add_argument("--reader-pages", type=int)
    parser.add_argument("--submission-pages", type=int)
    parser.add_argument("--depth-trigger-pages", type=int, default=14)
    parser.add_argument("--depth-trigger-chars", type=int, default=10000)
    parser.add_argument("--min-question-chars", type=int, default=800)
    parser.add_argument("--min-question-equations", type=int, default=1)
    parser.add_argument("--min-body-tables", type=int, default=3)
    parser.add_argument("--min-abstract-chars", type=int, default=550)
    parser.add_argument("--min-abstract-numbered-values", type=int, default=4)
    parser.add_argument("--min-evaluation-chars", type=int, default=200)
    parser.add_argument("--min-references", type=int, default=3)
    parser.add_argument("--appendix-required", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument(
        "--literature-library",
        type=Path,
        default=DEFAULT_LITERATURE_LIBRARY,
        help="references/literature-library.md 路径；核验每条参考文献可追溯。"
        "默认取本脚本旁的 ../references/literature-library.md——反编造校验必须默认开启，"
        "此前它是可选参数且四处文档化命令都不传，等于默认关闭",
    )
    parser.add_argument(
        "--results-ledger",
        type=Path,
        help="RESULTS.md 路径；核验每条 R-id 的数值确实进了论文（终检清单「正文数字 = RESULTS.md」的机检版）",
    )
    parser.add_argument(
        "--citation-log",
        type=Path,
        help="SOURCES.md 等实访记录；库外条目凭它证明 DOI 被实际访问过",
    )
    parser.add_argument(
        "--target-check",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="核查 rubric-and-writing.md §四的写作目标；只出 warning，不阻断",
    )
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors: list[dict[str, str]] = []
    expansions: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    reader_text, reader_error = read_document(args.reader)
    if reader_error:
        add_issue(errors, "MISSING_OR_UNREADABLE_READER", reader_error)
    submission_text, submission_error = read_document(args.submission)
    if submission_error:
        add_issue(errors, "MISSING_OR_UNREADABLE_SUBMISSION", submission_error)

    coverage_rows, coverage_error = read_csv(args.coverage, COVERAGE_COLUMNS)
    if coverage_error:
        add_issue(errors, "MISSING_OR_INVALID_COVERAGE_LEDGER", coverage_error)
        human_state = "PENDING"
    else:
        human_state = validate_coverage(coverage_rows, reader_text, errors, expansions)
    rubric_rows, rubric_error = read_csv(args.rubric, RUBRIC_COLUMNS)
    if rubric_error:
        add_issue(errors, "MISSING_OR_INVALID_RUBRIC", rubric_error)
        rubric_total = 0.0
    else:
        rubric_total = validate_rubric(rubric_rows, args.target_score, errors, expansions)

    if not reader_error and not submission_error:
        validate_editions(
            reader_text,
            submission_text,
            args.source_root,
            args.source_exclude,
            args.support_root,
            args.appendix_required,
            errors,
            warnings,
        )

    reader_pages = args.reader_pages
    if reader_pages is None:
        reader_pages, page_error = pdf_pages(args.reader)
        if page_error:
            add_issue(warnings, "PAGE_COUNT_UNAVAILABLE", page_error)
    if reader_pages is not None and reader_pages > args.max_body_pages:
        add_issue(errors, "READER_PAGE_LIMIT_EXCEEDED", f"阅读版 {reader_pages} 页 > 正文上限 {args.max_body_pages} 页")
    depth_metrics: dict[str, object] | None = None
    if not reader_error:
        depth_metrics = assess_depth(
            reader_text,
            reader_pages,
            coverage_rows if not coverage_error else None,
            args,
            expansions,
            warnings,
        )
    reference_check: dict[str, object] | None = None
    target_check: dict[str, object] | None = None
    results_check: dict[str, object] | None = None
    pagination_check: dict[str, object] | None = None
    if not reader_error:
        norm_text, positions = build_normalized_index(reader_text)
        reference_check = validate_references(
            extract_reference_entries(reader_text, norm_text, positions),
            args.literature_library,
            args.citation_log,
            errors,
            warnings,
            library_explicit=args.literature_library != DEFAULT_LITERATURE_LIBRARY,
        )
        pagination_check = validate_pagination(
            args.submission, submission_text, errors, warnings
        )
        results_check = validate_results_ledger(
            args.results_ledger, reader_text, errors, warnings
        )
        if args.target_check and depth_metrics is not None:
            target_check = assess_targets(
                depth_metrics,
                count_keywords(reader_text, norm_text, positions),
                count_figures(reader_text),
                warnings,
            )

    submission_pages = args.submission_pages
    if submission_pages is None:
        submission_pages, page_error = pdf_pages(args.submission)
        if page_error:
            add_issue(warnings, "SUBMISSION_PAGE_COUNT_UNAVAILABLE", page_error)

    if not expansions:
        # 深度诊断文案不得指向一个空列表：本轮若因 errors 提前失败而未产出 expansion
        # 项，必须说明「为什么这里是空的」，否则读者会去查一个不存在的清单。
        for warning in warnings:
            if warning["code"] == "DEPTH_REVIEW_REQUIRED" and "expansion_items" in warning["message"]:
                warning["message"] = warning["message"].replace(
                    "详见 expansion_items",
                    "本轮 expansion_items 为空（存在 errors 时深度形态项可能未能计算），先修 errors 再重跑契约",
                )

    if errors:
        status = "FAIL_CONTRACT"
    elif expansions:
        status = "NEEDS_EXPANSION"
    elif human_state == "HUMAN_ACCEPTED":
        status = "PASS"
    elif human_state == "PROXY_REHEARSAL":
        status = "PROXY_REHEARSAL"
    else:
        status = "NEEDS_HUMAN"

    report = {
        "schema_version": 1,
        "status": status,
        "rubric_total": rubric_total,
        "target_score": args.target_score,
        "reader_pages": reader_pages,
        "submission_pages": submission_pages,
        "human_state": human_state,
        "depth_metrics": depth_metrics,
        "reference_check": reference_check,
        "results_check": results_check,
        "pagination_check": pagination_check,
        "target_check": target_check,
        "errors": errors,
        "expansion_items": expansions,
        "warnings": warnings,
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if status in {"PASS", "PROXY_REHEARSAL"}:
        return 0
    if status in {"NEEDS_HUMAN", "NEEDS_EXPANSION"}:
        return 2
    return 1


if __name__ == "__main__":
    sys.exit(main())
