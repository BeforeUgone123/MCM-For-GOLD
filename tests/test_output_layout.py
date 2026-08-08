import importlib.util
import io
import json
import contextlib
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INITIALIZER = ROOT / "skills/mcm-gold/templates/init_result_workspace.py"
LAYOUT_VERIFIER = ROOT / "skills/mcm-gold/templates/verify_output_layout.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载 {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_initializer():
    return _load(INITIALIZER, "init_result_workspace")


def load_layout_verifier():
    return _load(LAYOUT_VERIFIER, "verify_output_layout")


def run_verifier(workspace: Path, write_index: bool = False) -> tuple[int, dict]:
    """跑一次校验，返回 (exit_code, report)。"""
    module = load_layout_verifier()
    argv = ["verify_output_layout.py", "--workspace", str(workspace)]
    if write_index:
        argv.append("--write-index")
    buffer = io.StringIO()
    old = sys.argv
    sys.argv = argv
    try:
        with contextlib.redirect_stdout(buffer):
            code = module.main()
    finally:
        sys.argv = old
    return code, json.loads(buffer.getvalue())


def make_workspace(tmp: str) -> Path:
    """最小合规工作区：七目录齐全，有论文、图+图源、台账、复现入口。"""
    root = Path(tmp) / "MCM-Result"
    module = load_initializer()
    module.initialize(Path(tmp))
    (root / "Paper-Outputs" / "paper").mkdir(parents=True, exist_ok=True)
    (root / "Paper-Outputs" / "paper" / "main.pdf").write_bytes(b"%PDF-1.4\n")
    (root / "Data-Figures" / "F-001-demo.pdf").write_bytes(b"%PDF-1.4\n")
    (root / "Data-Figures" / "F-001-demo.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    (root / "Intermediate-Outputs" / "RESULTS.md").write_text("# RESULTS\n", encoding="utf-8")
    (root / "Data-Scripts" / "run_all.py").write_text("# entry\n", encoding="utf-8")
    return root


def error_codes(report: dict) -> set[str]:
    return {line.split()[0] for line in report["errors"]}


def warning_codes(report: dict) -> set[str]:
    return {line.split()[0] for line in report["warnings"]}


class OutputLayoutTests(unittest.TestCase):
    def test_initializer_creates_exact_canonical_directories(self) -> None:
        module = load_initializer()
        with tempfile.TemporaryDirectory() as tmp:
            result = module.initialize(Path(tmp))
            root = Path(result["result_root"])
            self.assertEqual(
                {path.name for path in root.iterdir()}, set(module.DIRECTORIES)
            )
            self.assertEqual(result["created"], list(module.DIRECTORIES))

    def test_initializer_is_idempotent(self) -> None:
        module = load_initializer()
        with tempfile.TemporaryDirectory() as tmp:
            module.initialize(Path(tmp))
            result = module.initialize(Path(tmp))
            self.assertEqual(result["created"], [])
            self.assertEqual(result["existing"], list(module.DIRECTORIES))

    def test_initializer_rejects_file_collision(self) -> None:
        module = load_initializer()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "MCM-Result"
            root.mkdir()
            (root / module.DIRECTORIES[0]).write_text("collision", encoding="utf-8")
            with self.assertRaises(SystemExit):
                module.initialize(Path(tmp))


class LayoutVerifierTests(unittest.TestCase):
    """双向测试：合规工作区必须过，每类违规必须被单独抓到。"""

    def test_clean_workspace_passes_after_index_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_workspace(tmp)
            run_verifier(root, write_index=True)
            code, report = run_verifier(root)
            self.assertEqual(code, 0, report["errors"])
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["index"]["status"], "FRESH")

    def test_venv_in_source_tree_is_reported_once_not_per_file(self) -> None:
        """一个 .venv 里有上千个 __pycache__；报告必须折叠到目录级，否则结论被噪音淹没。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = make_workspace(tmp)
            deep = root / "Data-Scripts" / ".venv" / "lib" / "site-packages"
            for pkg in ("numpy", "pandas", "scipy"):
                (deep / pkg / "__pycache__").mkdir(parents=True)
                (deep / pkg / "__pycache__" / "x.cpython-313.pyc").write_bytes(b"\x00")
            code, report = run_verifier(root)
            self.assertEqual(code, 1)
            self.assertIn("CACHE_IN_SOURCE_TREE", error_codes(report))
            self.assertEqual(report["cache_outside_intermediate"], ["Data-Scripts/.venv/"])

    def test_cache_under_intermediate_outputs_is_allowed(self) -> None:
        """契约规定缓存归 Intermediate-Outputs/，那里有 venv 不算违规。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = make_workspace(tmp)
            (root / "Intermediate-Outputs" / "venv" / "lib").mkdir(parents=True)
            (root / "Intermediate-Outputs" / "venv" / "lib" / "a.pyc").write_bytes(b"\x00")
            _, report = run_verifier(root)
            self.assertEqual(report["cache_outside_intermediate"], [])
            self.assertNotIn("CACHE_IN_SOURCE_TREE", error_codes(report))

    def test_latex_build_artifacts_in_paper_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_workspace(tmp)
            paper = root / "Paper-Outputs" / "paper"
            (paper / "main.aux").write_text("", encoding="utf-8")
            (paper / "main.log").write_text("", encoding="utf-8")
            (paper / "main.synctex.gz").write_bytes(b"\x1f\x8b")
            code, report = run_verifier(root)
            self.assertEqual(code, 1)
            self.assertIn("BUILD_ARTIFACT_IN_DELIVERABLE", error_codes(report))
            self.assertEqual(
                report["build_artifacts_in_deliverables"],
                ["Paper-Outputs/paper/main.aux",
                 "Paper-Outputs/paper/main.log",
                 "Paper-Outputs/paper/main.synctex.gz"],
            )

    def test_eighth_top_level_directory_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_workspace(tmp)
            (root / "figures").mkdir()
            code, report = run_verifier(root)
            self.assertEqual(code, 1)
            self.assertIn("UNKNOWN_TOP_LEVEL_DIR", error_codes(report))
            self.assertEqual(report["extra_top_level_dirs"], ["figures"])

    def test_missing_ledger_errors_only_after_paper_exists(self) -> None:
        """论文在、台账不在 = 数值无来源，是错误；两者都不在只是早期状态。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = make_workspace(tmp)
            (root / "Intermediate-Outputs" / "RESULTS.md").unlink()
            code, report = run_verifier(root)
            self.assertEqual(code, 1)
            self.assertIn("EVIDENCE_LEDGER_MISSING", error_codes(report))

            (root / "Paper-Outputs" / "paper" / "main.pdf").unlink()
            code, report = run_verifier(root)
            self.assertNotIn("EVIDENCE_LEDGER_MISSING", error_codes(report))
            self.assertIn("EVIDENCE_LEDGER_ABSENT", warning_codes(report))

    def test_index_goes_stale_when_products_change_or_hand_edited(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_workspace(tmp)
            run_verifier(root, write_index=True)

            (root / "Data-Figures" / "F-002-new.pdf").write_bytes(b"%PDF-1.4\n")
            code, report = run_verifier(root)
            self.assertEqual(code, 1)
            self.assertIn("REVIEW_INDEX_STALE", error_codes(report))

            run_verifier(root, write_index=True)
            index = root / "README.md"
            index.write_text(index.read_text(encoding="utf-8").replace(
                "review 从这里开始", "手改过的标题"), encoding="utf-8")
            code, report = run_verifier(root)
            self.assertEqual(code, 1)
            self.assertIn("REVIEW_INDEX_STALE", error_codes(report))

    def test_index_records_missing_products_instead_of_omitting_them(self) -> None:
        """缺失必须可见：没有支撑包就要写「未生成」，不能默默不提。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = make_workspace(tmp)
            run_verifier(root, write_index=True)
            text = (root / "README.md").read_text(encoding="utf-8")
            self.assertIn("支撑材料包", text)
            self.assertIn("**未生成**", text)
            self.assertIn("F-001-demo.csv", text)

    def test_figure_without_source_table_is_flagged_in_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = make_workspace(tmp)
            (root / "Data-Figures" / "F-001-demo.csv").unlink()
            run_verifier(root, write_index=True)
            text = (root / "README.md").read_text(encoding="utf-8")
            self.assertIn("1 张缺图源表", text)

    def test_missing_workspace_returns_distinct_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            code, report = run_verifier(Path(tmp) / "nope")
            self.assertEqual(code, 2)
            self.assertEqual(report["status"], "WORKSPACE_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
