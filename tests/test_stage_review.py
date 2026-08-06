import csv
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "skills/mcm-gold/templates/verify_stage_review.py"


def load_verifier():
    spec = importlib.util.spec_from_file_location("verify_stage_review", VERIFIER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载 {VERIFIER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_case(
    directory: Path,
    stage: str,
    row_override: tuple[str, dict[str, str]] | None = None,
    summary_override: dict[str, object] | None = None,
) -> tuple[Path, Path]:
    module = load_verifier()
    score_path = directory / f"{stage}_REVIEW_SCORE_R1.csv"
    summary_path = directory / f"{stage}_REVIEW_SUMMARY_R1.json"
    fieldnames = sorted(module.REQUIRED_COLUMNS)
    rows = []
    for criterion_id, weight in module.expected_criteria(stage).items():
        derived = stage == "T7" and criterion_id.startswith("T7-")
        row = {
            "review_id": f"{stage}-R1",
            "stage": stage,
            "criterion_id": criterion_id,
            "scope": "universal" if criterion_id.startswith("U-") else "stage_specific",
            "criterion": f"核验 {criterion_id}",
            "weight": str(weight),
            "level": "DERIVED" if derived else "VERIFIED",
            "multiplier": "1",
            "score": str(weight),
            "observed": f"实际读取并核对 {criterion_id} 对应工件",
            "evidence_paths": f"MCM-Result/Review-Results/{criterion_id}.json",
            "evidence_ids": "R-001",
            "gate_refs": f"{stage}-G1",
            "deduction_reason": "",
            "repair_action": "",
            "reviewer_id": "reviewer-1",
            "source_review_ids": f"{stage}-R1",
            "producer_context_id": "producer-context",
            "reviewer_context_id": "reviewer-context",
            "reviewed_at": "2026-09-11T12:00:00+08:00",
        }
        if row_override and row_override[0] == criterion_id:
            row.update(row_override[1])
        rows.append(row)
    with score_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    gates = [
        {
            "gate_id": f"{stage}-G{number}",
            "status": "PASS",
            "evidence": [f"MCM-Result/Review-Results/{stage}-G{number}.json"],
        }
        for number in range(1, module.HARD_GATES[stage] + 1)
    ]
    summary = {
        "schema_version": "1.0",
        "review_run_id": f"{stage}-R1",
        "review_kind": "R1",
        "stage": stage,
        "review_mode": "standard",
        "producer_context_id": "producer-context",
        "reviewer_context_id": "reviewer-context",
        "review_independence": "independent_context",
        "scores": {"universal": 30, "stage_specific": 70, "total": 100},
        "hard_gates": gates,
        "requires_second_review": stage in {"T6", "T7", "T8"},
        "review_conflict": False,
        "status": "PASS",
        "limitations": [],
        "top_repairs": [],
        "source_score_file": score_path.name,
        "source_reviews": [f"{stage}-R1"],
        "generated_at": "2026-09-11T12:00:00+08:00",
    }
    if summary_override:
        summary.update(summary_override)
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return score_path, summary_path


def run_verifier(stage: str, score: Path, summary: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(VERIFIER),
            "--stage",
            stage,
            "--score",
            str(score),
            "--summary",
            str(summary),
        ],
        capture_output=True,
        text=True,
    )


class StageReviewTests(unittest.TestCase):
    def test_complete_t0_review_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            score, summary = write_case(Path(tmp), "T0")
            result = run_verifier("T0", score, summary)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_anchor_multiplier_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            score, summary = write_case(
                Path(tmp), "T0", ("U-01", {"level": "PRESENT", "multiplier": "1"})
            )
            result = run_verifier("T0", score, summary)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("multiplier", result.stdout)

    def test_hard_gate_failure_cannot_be_scored_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            score, summary = write_case(Path(tmp), "T0")
            data = json.loads(summary.read_text(encoding="utf-8"))
            data["hard_gates"][0]["status"] = "FAIL"
            summary.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            result = run_verifier("T0", score, summary)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("BLOCKED", result.stdout)

    def test_t7_derived_rubric_scores_are_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            score, summary = write_case(Path(tmp), "T7")
            result = run_verifier("T7", score, summary)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
