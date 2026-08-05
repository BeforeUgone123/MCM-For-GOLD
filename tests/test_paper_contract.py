import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/mcm-gold/templates/verify_paper_contract.py"
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
RUBRIC_COLUMNS = [
    "dimension",
    "score",
    "max_score",
    "pass_score",
    "evidence",
    "observed",
    "status",
]
ANCHORS = {
    "interface": "问题一任务接口",
    "definition": "问题一数学定义",
    "algorithm": "问题一求解算法",
    "result": "问题一结果表",
    "validation": "问题一稳健性检验",
    "boundary": "问题一解释边界",
}
RUBRIC = [
    ("摘要页", 15, 15, 10),
    ("问题分析与假设", 9, 10, 6),
    ("模型建立", 23, 25, 16),
    ("求解与结果正确性", 20, 22, 15),
    ("检验与稳健性", 11, 13, 8),
    ("写作与图表", 10, 12, 8),
    ("合规与附录", 3, 3, 3),
]


def write_csv(path: Path, columns: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


class PaperContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.reader = self.root / "main.txt"
        self.submission = self.root / "paper_submission.txt"
        self.coverage = self.root / "PAPER_COVERAGE_LEDGER.csv"
        self.rubric = self.root / "T7_RUBRIC_REVIEW.csv"
        self.source = self.root / "support"
        self.source.mkdir()
        (self.source / "solve.py").write_text(
            "def solve(data):\n    result = compute_solution(data, seed=2024)\n    return result\n",
            encoding="utf-8",
        )
        body = "\n".join(ANCHORS.values()) + "\n"
        self.reader.write_text(body, encoding="utf-8")
        self.submission.write_text(
            body
            + "附录 A 支撑材料文件列表\n"
            + "solve.py\n"
            + "附录 B 完整源程序\n"
            + "solve.py\n"
            + "result = compute_solution(data, seed=2024)\n",
            encoding="utf-8",
        )
        self.coverage_rows = []
        for component, anchor in ANCHORS.items():
            self.coverage_rows.append(
                {
                    "question_id": "Q1",
                    "component": component,
                    "required_content": f"Q1 {component} 的实质内容",
                    "claim_or_risk_ids": "K-001" if component == "validation" else "C-001",
                    "paper_anchor": anchor,
                    "evidence_ids": "R-002" if component == "validation" else ("R-001" if component == "result" else "C-001"),
                    "observed": f"已在 {anchor} 回读",
                    "status": "PASS",
                    "human_status": "HUMAN_ACCEPTED",
                }
            )
        self.write_valid_files()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_valid_files(self) -> None:
        write_csv(self.coverage, COVERAGE_COLUMNS, self.coverage_rows)
        write_csv(
            self.rubric,
            RUBRIC_COLUMNS,
            [
                {
                    "dimension": name,
                    "score": score,
                    "max_score": maximum,
                    "pass_score": passing,
                    "evidence": f"{name}页/图/表锚点",
                    "observed": f"实读得分 {score}",
                    "status": "PASS" if score >= passing else "FAIL",
                }
                for name, score, maximum, passing in RUBRIC
            ],
        )

    def run_contract(self, *extra: str) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
        command = [
            sys.executable,
            str(SCRIPT),
            "--coverage",
            str(self.coverage),
            "--rubric",
            str(self.rubric),
            "--reader",
            str(self.reader),
            "--submission",
            str(self.submission),
            "--source-root",
            str(self.source),
            "--support-root",
            str(self.source),
            "--reader-pages",
            "18",
            "--submission-pages",
            "21",
            *extra,
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        return result, json.loads(result.stdout)

    def test_complete_contract_passes(self) -> None:
        result, report = self.run_contract()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["rubric_total"], 91)

    def test_concise_complete_paper_only_warns(self) -> None:
        result, report = self.run_contract("--reader-pages", "11")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["status"], "PASS")
        self.assertIn("DEPTH_REVIEW_REQUIRED", {item["code"] for item in report["warnings"]})

    def test_missing_component_fails_contract(self) -> None:
        self.coverage_rows.pop()
        self.write_valid_files()
        result, report = self.run_contract()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(report["status"], "FAIL_CONTRACT")
        self.assertIn("MISSING_COMPONENT", {item["code"] for item in report["errors"]})

    def test_weak_coverage_routes_to_expansion(self) -> None:
        self.coverage_rows[2]["status"] = "WEAK"
        self.write_valid_files()
        result, report = self.run_contract()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(report["status"], "NEEDS_EXPANSION")

    def test_invented_four_dimension_rubric_is_rejected(self) -> None:
        rows = []
        for name, score, maximum, passing in RUBRIC[:4]:
            rows.append(
                {
                    "dimension": name,
                    "score": score,
                    "max_score": maximum,
                    "pass_score": passing,
                    "evidence": "anchor",
                    "observed": "checked",
                    "status": "PASS",
                }
            )
        write_csv(self.rubric, RUBRIC_COLUMNS, rows)
        result, report = self.run_contract()
        self.assertEqual(result.returncode, 1)
        self.assertIn("MISSING_RUBRIC_DIMENSION", {item["code"] for item in report["errors"]})

    def test_below_target_cannot_pass(self) -> None:
        lowered = list(RUBRIC)
        lowered[2] = ("模型建立", 18, 25, 16)
        write_csv(
            self.rubric,
            RUBRIC_COLUMNS,
            [
                {
                    "dimension": name,
                    "score": score,
                    "max_score": maximum,
                    "pass_score": passing,
                    "evidence": "anchor",
                    "observed": "checked",
                    "status": "PASS",
                }
                for name, score, maximum, passing in lowered
            ],
        )
        result, report = self.run_contract()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(report["status"], "NEEDS_EXPANSION")
        self.assertIn("RUBRIC_BELOW_TARGET", {item["code"] for item in report["expansion_items"]})

    def test_missing_submission_fails_contract(self) -> None:
        self.submission.unlink()
        result, report = self.run_contract()
        self.assertEqual(result.returncode, 1)
        self.assertIn("MISSING_OR_UNREADABLE_SUBMISSION", {item["code"] for item in report["errors"]})

    def test_file_list_without_source_content_fails(self) -> None:
        body = self.reader.read_text(encoding="utf-8")
        self.submission.write_text(
            body + "附录 A 支撑材料文件列表\nsolve.py\n附录 B 完整源程序\nsolve.py\n",
            encoding="utf-8",
        )
        result, report = self.run_contract()
        self.assertEqual(result.returncode, 1)
        self.assertIn("SOURCE_CONTENT_NOT_EMBEDDED", {item["code"] for item in report["errors"]})

    def test_reader_submission_body_drift_fails(self) -> None:
        text = self.submission.read_text(encoding="utf-8")
        self.submission.write_text("提交版擅自改写正文\n" + text, encoding="utf-8")
        result, report = self.run_contract()
        self.assertEqual(result.returncode, 1)
        self.assertIn("SCIENTIFIC_BODY_DRIFT", {item["code"] for item in report["errors"]})

    def test_no_appendix_mode_still_compares_bodies(self) -> None:
        self.submission.write_text(
            self.reader.read_text(encoding="utf-8") + "科学正文漂移\n",
            encoding="utf-8",
        )
        result, report = self.run_contract("--no-appendix-required")
        self.assertEqual(result.returncode, 1)
        self.assertIn("SCIENTIFIC_BODY_DRIFT", {item["code"] for item in report["errors"]})

    def test_pdf_formula_extraction_reordering_only_warns(self) -> None:
        body = "\n".join(ANCHORS.values()) + "\n" + "共同科学正文" * 1000 + "公式ABC≥DEF\n"
        self.reader.write_text(body, encoding="utf-8")
        submission_body = body.replace("公式ABC≥DEF", "公式ABCDE≥F")
        self.submission.write_text(
            submission_body
            + "附录 A 支撑材料文件列表\n"
            + "solve.py\n"
            + "附录 B 完整源程序\n"
            + "solve.py\n"
            + "result = compute_solution(data, seed=2024)\n",
            encoding="utf-8",
        )
        result, report = self.run_contract()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["status"], "PASS")
        self.assertIn("PDF_TEXT_ORDER_VARIANCE", {item["code"] for item in report["warnings"]})

    def test_pending_human_review_cannot_pass(self) -> None:
        for row in self.coverage_rows:
            row["human_status"] = "PENDING"
        self.write_valid_files()
        result, report = self.run_contract()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(report["status"], "NEEDS_HUMAN")

    def test_compound_historical_ids_are_accepted(self) -> None:
        for row in self.coverage_rows:
            row["claim_or_risk_ids"] = "K-D201" if row["component"] == "validation" else "C-D101"
            if row["component"] in {"result", "validation"}:
                row["evidence_ids"] = "R-D301"
        self.write_valid_files()
        result, report = self.run_contract()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["status"], "PASS")

    def test_reader_page_limit_is_hard_failure(self) -> None:
        result, report = self.run_contract("--reader-pages", "31")
        self.assertEqual(result.returncode, 1)
        self.assertIn("READER_PAGE_LIMIT_EXCEEDED", {item["code"] for item in report["errors"]})

    def test_proxy_rehearsal_never_becomes_formal_pass(self) -> None:
        for row in self.coverage_rows:
            row["human_status"] = "PROXY_REHEARSAL"
        self.write_valid_files()
        result, report = self.run_contract()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["status"], "PROXY_REHEARSAL")


if __name__ == "__main__":
    unittest.main()
