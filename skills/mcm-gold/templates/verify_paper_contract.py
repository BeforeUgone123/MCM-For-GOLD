#!/usr/bin/env python3
"""Verify T7/T8 paper coverage, rubric, and reader/submission closure."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from difflib import SequenceMatcher
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
VALIDATION_ID_RE = re.compile(rf"\b(?:R|P|V)-{ID_SUFFIX}\b", re.IGNORECASE)
DECISION_ID_RE = re.compile(rf"\bD-{ID_SUFFIX}\b", re.IGNORECASE)
CJK_RE = re.compile(r"[一-鿿]")
EQUATION_NUMBER_RE = re.compile(r"[（(]\s*\d+(?:\.\d+)?\s*[)）]\s*$")
TABLE_LABEL_RE = re.compile(r"表\s*(\d+(?:[-–.]\d+)?)")
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


def count_references(reader_text: str, norm_text: str, positions: list[int]) -> tuple[int, bool]:
    heading = find_raw_position(norm_text, positions, REFERENCE_HEADING)
    if not heading:
        return len(REFERENCE_ENTRY_RE.findall(reader_text)), False
    end = len(reader_text)
    appendix = find_raw_position(norm_text, positions, APPENDIX_HEADING)
    if appendix and appendix[0] > heading[1]:
        end = appendix[0]
    return len(REFERENCE_ENTRY_RE.findall(reader_text[heading[1]:end])), True


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
        if status != "N_A" and (not anchor or normalize(anchor) not in reader_normalized):
            add_issue(errors, "ANCHOR_NOT_FOUND", f"{question}/{component} 的 paper_anchor 无法在阅读版检索：{anchor or '<empty>'}")
        if component == "validation":
            if not RISK_ID_RE.search(row["claim_or_risk_ids"]):
                add_issue(errors, "VALIDATION_WITHOUT_RISK", f"{question}/validation 未关联 K-id")
            if status != "N_A" and not VALIDATION_ID_RE.search(row["evidence_ids"]):
                add_issue(errors, "VALIDATION_WITHOUT_EVIDENCE", f"{question}/validation 未关联 R/P/V-id")
        if component == "result" and not VALIDATION_ID_RE.search(row["evidence_ids"]):
            add_issue(errors, "RESULT_WITHOUT_EVIDENCE", f"{question}/result 未关联 R/P/V-id")
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
    support_root: Path | None,
    appendix_required: bool,
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
) -> None:
    if appendix_required:
        markers = ["附录 A", "附录A", "支撑材料文件列表"]
        positions = [submission_text.find(marker) for marker in markers if marker in submission_text]
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
        else:
            add_issue(errors, "SCIENTIFIC_BODY_DRIFT", "阅读版与提交版的共享科学正文不一致")
    if not appendix_required:
        return
    if "源程序" not in submission_text:
        add_issue(errors, "MISSING_SOURCE_APPENDIX", "提交版缺完整源程序附录")
    normalized_submission = normalize(submission_text)
    if support_root is not None:
        if not support_root.is_dir():
            add_issue(errors, "MISSING_SUPPORT_ROOT", f"支撑目录不存在：{support_root}")
        else:
            for path in visible_files(support_root):
                relative = path.relative_to(support_root).as_posix()
                if normalize(relative) not in normalized_submission:
                    add_issue(errors, "SUPPORT_FILE_NOT_LISTED", f"提交版文件列表未找到：{relative}")
    if source_root is not None:
        if not source_root.is_dir():
            add_issue(errors, "MISSING_SOURCE_ROOT", f"源程序目录不存在：{source_root}")
        else:
            code_files = [path for path in visible_files(source_root) if path.suffix.lower() in CODE_SUFFIXES]
            if not code_files:
                add_issue(errors, "NO_SOURCE_FILES", f"源程序目录没有可识别代码：{source_root}")
            for path in code_files:
                relative = path.relative_to(source_root).as_posix()
                if normalize(relative) not in normalized_submission and normalize(path.name) not in normalized_submission:
                    add_issue(errors, "SOURCE_FILE_NOT_NAMED", f"提交版未出现源文件名：{relative}")
                    continue
                signature = source_signature(path)
                if signature and normalize(signature) not in normalized_submission:
                    add_issue(errors, "SOURCE_CONTENT_NOT_EMBEDDED", f"提交版未回读到 {relative} 的代码内容")


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
    if abstract["located"]:
        if (
            abstract["cjk_chars"] < args.min_abstract_chars
            or abstract["unit_values"] < args.min_abstract_numbered_values
        ):
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

    form_failed = False
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coverage", type=Path, required=True)
    parser.add_argument("--rubric", type=Path, required=True)
    parser.add_argument("--reader", type=Path, required=True)
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--source-root", type=Path)
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
    submission_pages = args.submission_pages
    if submission_pages is None:
        submission_pages, page_error = pdf_pages(args.submission)
        if page_error:
            add_issue(warnings, "SUBMISSION_PAGE_COUNT_UNAVAILABLE", page_error)

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
