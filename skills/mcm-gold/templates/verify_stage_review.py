#!/usr/bin/env python3
"""Validate one MCM Gold stage review score sheet and summary."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path


ANCHORS = {
    "MISSING": Decimal("0"),
    "PRESENT": Decimal("0.5"),
    "VERIFIED_LIMITED": Decimal("0.8"),
    "VERIFIED": Decimal("1"),
}
UNIVERSAL = {f"U-{number:02d}": Decimal("5") for number in range(1, 7)}
STAGE_CRITERIA = {
    "T0": [15, 15, 20, 10, 10],
    "T1": [20, 15, 10, 15, 10],
    "T2": [15, 20, 10, 10, 10, 5],
    "T3": [10, 15, 15, 15, 5, 10],
    "T4": [10, 10, 15, 10, 15, 10],
    "T5": [15, 15, 10, 10, 10, 10],
    "T6": [10, 10, 10, 10, 10, 10, 10],
    "T7": [Decimal("10.5"), 7, Decimal("17.5"), Decimal("15.4"), Decimal("9.1"), Decimal("8.4"), Decimal("2.1")],
    "T8": [10, 10, 10, 20, 10, 10],
}
HARD_GATES = {
    "T0": 4,
    "T1": 4,
    "T2": 5,
    "T3": 6,
    "T4": 4,
    "T5": 6,
    "T6": 5,
    "T7": 6,
    "T8": 7,
}
REQUIRED_COLUMNS = {
    "review_id",
    "stage",
    "criterion_id",
    "scope",
    "criterion",
    "weight",
    "level",
    "multiplier",
    "score",
    "observed",
    "evidence_paths",
    "evidence_ids",
    "gate_refs",
    "deduction_reason",
    "repair_action",
    "reviewer_id",
    "source_review_ids",
    "producer_context_id",
    "reviewer_context_id",
    "reviewed_at",
}
VAGUE_OBSERVATIONS = {"已检查", "质量良好", "符合要求", "通过", "pass"}


def as_decimal(value: object, field: str, errors: list[str]) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        errors.append(f"{field} 不是有效数字: {value!r}")
        return Decimal("0")


def expected_criteria(stage: str) -> dict[str, Decimal]:
    stage_rows = {
        f"{stage}-{index:02d}": Decimal(str(weight))
        for index, weight in enumerate(STAGE_CRITERIA[stage], start=1)
    }
    return {**UNIVERSAL, **stage_rows}


def validate_score(path: Path, stage: str) -> tuple[list[str], dict[str, Decimal], dict[str, str]]:
    errors: list[str] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing_columns = REQUIRED_COLUMNS - columns
        if missing_columns:
            errors.append(f"SCORE 缺少列: {sorted(missing_columns)}")
        rows = list(reader)

    expected = expected_criteria(stage)
    seen: dict[str, dict[str, str]] = {}
    totals = {"universal": Decimal("0"), "stage_specific": Decimal("0")}
    metadata: dict[str, str] = {}

    for line_number, row in enumerate(rows, start=2):
        criterion_id = row.get("criterion_id", "").strip()
        if not criterion_id:
            errors.append(f"SCORE:{line_number} 缺 criterion_id")
            continue
        if criterion_id in seen:
            errors.append(f"SCORE:{line_number} criterion_id 重复: {criterion_id}")
            continue
        seen[criterion_id] = row

        if row.get("stage", "").strip() != stage:
            errors.append(f"SCORE:{line_number} stage 不是 {stage}")
        if criterion_id not in expected:
            errors.append(f"SCORE:{line_number} 未知评分项: {criterion_id}")
            continue

        expected_scope = "universal" if criterion_id.startswith("U-") else "stage_specific"
        scope = row.get("scope", "").strip()
        if scope != expected_scope:
            errors.append(f"SCORE:{line_number} {criterion_id} scope 应为 {expected_scope}")

        weight = as_decimal(row.get("weight", ""), f"SCORE:{line_number} weight", errors)
        if weight != expected[criterion_id]:
            errors.append(
                f"SCORE:{line_number} {criterion_id} 权重 {weight} != {expected[criterion_id]}"
            )

        level = row.get("level", "").strip()
        multiplier = as_decimal(
            row.get("multiplier", ""), f"SCORE:{line_number} multiplier", errors
        )
        if stage == "T7" and expected_scope == "stage_specific":
            if level != "DERIVED":
                errors.append(f"SCORE:{line_number} T7 专属项必须使用 DERIVED")
            if not Decimal("0") <= multiplier <= Decimal("1"):
                errors.append(f"SCORE:{line_number} DERIVED multiplier 必须在 0 到 1")
        else:
            if level not in ANCHORS:
                errors.append(f"SCORE:{line_number} 非法 level: {level}")
            elif multiplier != ANCHORS[level]:
                errors.append(
                    f"SCORE:{line_number} {level} multiplier 应为 {ANCHORS[level]}"
                )

        score = as_decimal(row.get("score", ""), f"SCORE:{line_number} score", errors)
        if abs(score - weight * multiplier) > Decimal("0.001"):
            errors.append(
                f"SCORE:{line_number} {criterion_id} score != weight * multiplier"
            )
        if scope in totals:
            totals[scope] += score

        observed = row.get("observed", "").strip()
        if not observed or observed.lower() in VAGUE_OBSERVATIONS:
            errors.append(f"SCORE:{line_number} observed 缺实际观察: {observed!r}")
        if level not in {"MISSING", ""} and not row.get("evidence_paths", "").strip():
            errors.append(f"SCORE:{line_number} 非 MISSING 项缺 evidence_paths")
        if not row.get("source_review_ids", "").strip():
            errors.append(f"SCORE:{line_number} 缺 source_review_ids")
        if row.get("producer_context_id", "").strip() == row.get(
            "reviewer_context_id", ""
        ).strip():
            errors.append(f"SCORE:{line_number} reviewer 与 producer 上下文相同")

        for key in (
            "review_id",
            "reviewer_id",
            "producer_context_id",
            "reviewer_context_id",
            "reviewed_at",
        ):
            value = row.get(key, "").strip()
            if not value:
                errors.append(f"SCORE:{line_number} 缺 {key}")
            elif key in metadata and metadata[key] != value:
                errors.append(f"SCORE:{line_number} {key} 在评分表内不一致")
            else:
                metadata[key] = value

    missing_criteria = set(expected) - set(seen)
    if missing_criteria:
        errors.append(f"SCORE 缺评分项: {sorted(missing_criteria)}")
    if sum(weight for key, weight in expected.items() if key.startswith("U-")) != Decimal("30"):
        errors.append("内部错误: 通用权重不等于 30")
    if sum(weight for key, weight in expected.items() if not key.startswith("U-")) != Decimal("70"):
        errors.append("内部错误: 阶段专属权重不等于 70")
    totals["total"] = totals["universal"] + totals["stage_specific"]
    return errors, totals, metadata


def expected_status(summary: dict[str, object], totals: dict[str, Decimal]) -> str:
    gates = summary.get("hard_gates", [])
    gate_statuses = {
        item.get("status") for item in gates if isinstance(item, dict)
    }
    if "FAIL" in gate_statuses:
        return "BLOCKED"
    if "PENDING_HUMAN" in gate_statuses or summary.get("review_conflict") is True:
        return "NEEDS_HUMAN"
    if (
        totals["total"] >= Decimal("85")
        and totals["universal"] >= Decimal("24")
        and totals["stage_specific"] >= Decimal("56")
    ):
        return "PASS"
    if (
        totals["total"] >= Decimal("70")
        and totals["universal"] >= Decimal("18")
        and totals["stage_specific"] >= Decimal("42")
    ):
        return "PASS_WITH_LIMITATIONS"
    return "BLOCKED"


def validate_summary(
    path: Path, stage: str, totals: dict[str, Decimal], metadata: dict[str, str]
) -> list[str]:
    errors: list[str] = []
    try:
        summary = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"SUMMARY 无法读取: {exc}"]

    if summary.get("schema_version") != "1.0":
        errors.append("SUMMARY schema_version 必须为 1.0")
    if summary.get("stage") != stage:
        errors.append(f"SUMMARY stage 必须为 {stage}")
    review_kind = summary.get("review_kind")
    if review_kind not in {"R1", "R2", "FINAL"}:
        errors.append("SUMMARY review_kind 必须为 R1、R2 或 FINAL")
    allowed_independence = {
        "independent_context",
        "independent_agent",
    }
    if review_kind == "FINAL":
        allowed_independence.add("independent_merge")
    if summary.get("review_independence") not in allowed_independence:
        errors.append("SUMMARY review_independence 不是正式独立 review")
    if summary.get("producer_context_id") == summary.get("reviewer_context_id"):
        errors.append("SUMMARY reviewer 与 producer 上下文相同")
    if metadata.get("producer_context_id") != summary.get("producer_context_id"):
        errors.append("SUMMARY producer_context_id 与 SCORE 不一致")
    if metadata.get("reviewer_context_id") != summary.get("reviewer_context_id"):
        errors.append("SUMMARY reviewer_context_id 与 SCORE 不一致")
    source_reviews = summary.get("source_reviews")
    if not isinstance(source_reviews, list) or not any(
        str(item).strip() for item in source_reviews
    ):
        errors.append("SUMMARY source_reviews 必须列出原始 review")
    elif review_kind in {"R1", "R2"} and summary.get("review_run_id") not in source_reviews:
        errors.append("SUMMARY 原始 review 的 source_reviews 必须包含自身 review_run_id")

    summary_scores = summary.get("scores")
    if not isinstance(summary_scores, dict):
        errors.append("SUMMARY 缺 scores 对象")
    else:
        for key in ("universal", "stage_specific", "total"):
            actual = as_decimal(summary_scores.get(key), f"SUMMARY scores.{key}", errors)
            if abs(actual - totals[key]) > Decimal("0.001"):
                errors.append(f"SUMMARY scores.{key} 与 SCORE 不一致")

    gates = summary.get("hard_gates")
    expected_gates = {f"{stage}-G{number}" for number in range(1, HARD_GATES[stage] + 1)}
    actual_gates: set[str] = set()
    if not isinstance(gates, list):
        errors.append("SUMMARY hard_gates 必须为数组")
    else:
        for index, gate in enumerate(gates):
            if not isinstance(gate, dict):
                errors.append(f"SUMMARY hard_gates[{index}] 不是对象")
                continue
            gate_id = str(gate.get("gate_id", ""))
            if gate_id in actual_gates:
                errors.append(f"SUMMARY hard gate 重复: {gate_id}")
            actual_gates.add(gate_id)
            if gate.get("status") not in {"PASS", "FAIL", "PENDING_HUMAN"}:
                errors.append(f"SUMMARY {gate_id} status 非法")
            evidence = gate.get("evidence")
            if not isinstance(evidence, list) or not any(str(item).strip() for item in evidence):
                errors.append(f"SUMMARY {gate_id} 缺 evidence")
        if actual_gates != expected_gates:
            errors.append(
                f"SUMMARY hard gate 集合错误: missing={sorted(expected_gates - actual_gates)}, "
                f"extra={sorted(actual_gates - expected_gates)}"
            )

    required_second = stage in {"T6", "T7", "T8"} or (
        stage in {"T0", "T1", "T2", "T3", "T4", "T5"}
        and Decimal("80") <= totals["total"] <= Decimal("90")
    )
    if summary.get("requires_second_review") is not required_second:
        errors.append(
            f"SUMMARY requires_second_review 应为 {str(required_second).lower()}"
        )

    derived_status = expected_status(summary, totals)
    if summary.get("status") != derived_status:
        errors.append(
            f"SUMMARY status={summary.get('status')}，按分数与门禁应为 {derived_status}"
        )
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="校验阶段 review 评分与摘要")
    parser.add_argument("--stage", required=True, choices=sorted(STAGE_CRITERIA))
    parser.add_argument("--score", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    args = parser.parse_args()

    errors, totals, metadata = validate_score(args.score, args.stage)
    if not errors:
        errors.extend(validate_summary(args.summary, args.stage, totals, metadata))

    result = {
        "status": "FAIL" if errors else "PASS",
        "stage": args.stage,
        "score_file": str(args.score),
        "summary_file": str(args.summary),
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
