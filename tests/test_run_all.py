import importlib.util
import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_ALL = ROOT / "skills/mcm-gold/templates/run_all.py"


class RunAllConcurrencyTests(unittest.TestCase):
    def test_duplicate_result_id_is_atomic_across_processes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            state_dir = tmp_path / "workspace"
            helper = tmp_path / "log_once.py"
            helper.write_text(
                textwrap.dedent(
                    f"""
                    import importlib.util
                    import pathlib
                    import time

                    spec = importlib.util.spec_from_file_location("run_all", {str(RUN_ALL)!r})
                    run_all = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(run_all)
                    run_all.STATE_DIR = pathlib.Path({str(state_dir)!r})

                    original_records = run_all._records
                    def delayed_records():
                        records = original_records()
                        time.sleep(0.15)
                        return records
                    run_all._records = delayed_records
                    run_all.log_result("R-001", "并发结果", 1, "test", 20260910)
                    """
                ),
                encoding="utf-8",
            )

            processes = [
                subprocess.Popen(
                    [sys.executable, str(helper)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                for _ in range(8)
            ]
            results = [process.communicate(timeout=10) for process in processes]
            return_codes = [process.returncode for process in processes]

            self.assertEqual(return_codes.count(0), 1, results)
            records = [
                json.loads(line)
                for line in (state_dir / "RESULTS.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual([record["id"] for record in records], ["R-001"])

    def test_parallel_unique_results_survive_in_jsonl_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            state_dir = tmp_path / "workspace"
            helper = tmp_path / "log_unique.py"
            helper.write_text(
                textwrap.dedent(
                    f"""
                    import importlib.util
                    import pathlib
                    import sys

                    spec = importlib.util.spec_from_file_location("run_all", {str(RUN_ALL)!r})
                    run_all = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(run_all)
                    run_all.STATE_DIR = pathlib.Path({str(state_dir)!r})
                    run_all.log_result(sys.argv[1], "并发结果", 1, "test", 20260910)
                    """
                ),
                encoding="utf-8",
            )
            ids = [f"R-{index:03d}" for index in range(1, 17)]
            processes = [
                subprocess.Popen(
                    [sys.executable, str(helper), rid],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                for rid in ids
            ]
            results = [process.communicate(timeout=10) for process in processes]
            self.assertTrue(all(process.returncode == 0 for process in processes), results)

            records = [
                json.loads(line)
                for line in (state_dir / "RESULTS.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual({record["id"] for record in records}, set(ids))
            markdown = (state_dir / "RESULTS.md").read_text(encoding="utf-8")
            for rid in ids:
                self.assertIn(rid, markdown)

    def test_confirm_preserves_computed_timestamp(self) -> None:
        spec = importlib.util.spec_from_file_location("run_all_for_confirm", RUN_ALL)
        run_all = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(run_all)
        with tempfile.TemporaryDirectory() as tmp:
            run_all.STATE_DIR = Path(tmp) / "workspace"
            run_all.log_result("R-001", "结果", 1, "test", 20260910)
            computed_at = run_all._records()[-1]["computed_at"]
            run_all.confirm_result("R-001", "manual-check", "CONFIRMED")
            confirmed = run_all._records()[-1]
            self.assertEqual(confirmed["computed_at"], computed_at)
            self.assertTrue(confirmed["verified_at"])
            self.assertEqual(confirmed["status"], "CONFIRMED")


if __name__ == "__main__":
    unittest.main()
