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


class ProblemEntrypointTests(unittest.TestCase):
    """--all 不得把「只跑了一部分」伪装成「全跑完」。

    实测事故：某次支撑包 src/ 下只有 p1.py，而 README 与论文附录都写着
    src/p1.py…src/p5.py。评委执行 --all，9.6 秒后看到 [DONE]，会认为五问
    全部复现，实际只跑了 1/5。缺少必要源程序与运行结果和论文不符都是
    格式规范第五条的取消资格红线，必须显性失败。
    """

    @staticmethod
    def _load():
        spec = importlib.util.spec_from_file_location("run_all", RUN_ALL)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _with_entries(self, names, fn):
        import os

        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            src.mkdir()
            for name in names:
                (src / name).write_text("def main(seed, log_result):\n    pass\n", encoding="utf-8")
            cwd = os.getcwd()
            os.chdir(tmp)
            try:
                return fn()
            finally:
                os.chdir(cwd)

    def test_gap_in_entrypoints_fails(self) -> None:
        module = self._load()
        with self.assertRaises(SystemExit) as caught:
            self._with_entries(
                ["p1.py", "p2.py", "p5.py"],
                lambda: module._problem_numbers(True, None),
            )
        self.assertIn("p3.py", str(caught.exception))
        self.assertIn("p4.py", str(caught.exception))

    def test_expect_problems_catches_wholesale_shortfall(self) -> None:
        """入口只有 p1.py 时编号是「连续」的，只有 --expect-problems 能抓到。"""
        module = self._load()
        with self.assertRaises(SystemExit) as caught:
            self._with_entries(
                ["p1.py"],
                lambda: module._problem_numbers(True, None, 5),
            )
        self.assertIn("5", str(caught.exception))

    def test_complete_entrypoints_pass(self) -> None:
        module = self._load()
        numbers = self._with_entries(
            ["p1.py", "p2.py", "p3.py", "p4.py", "p5.py"],
            lambda: module._problem_numbers(True, None, 5),
        )
        self.assertEqual(numbers, [1, 2, 3, 4, 5])
