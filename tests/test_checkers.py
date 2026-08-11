"""守护检查器本身。

起因是一次实测事故：给 `verify_output_layout.py` 加检查时忘了 `import re`，模块顶层的
`re.compile` 立刻 NameError。脚本对四个真实工作区全部崩溃，而崩溃输出里 grep 不到
`FOREIGN_TOPIC_CONTENT`，看上去恰好就是「零误报」——差一点被当成检查通过。
`validate_skill_group.py` 当时也照样 PASS，因为它只看文档链接与元数据，不碰脚本。

所以第一组测试只做一件事：**每个 templates/*.py 都必须能 import、`--help` 都必须 exit 0**。
这一条就能挡住那类错误。第二组把本轮四个新检查器的核心失效路径固化下来，
它们此前只用一次性的手工 fixture 验过，验完即弃。
"""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "skills/mcm-gold/templates"

# run_all.py 是给工作区用的复现入口，import 它会带起状态目录副作用，另有专测
IMPORT_EXEMPT = {"run_all.py"}


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载 {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(TEMPLATES / script), *args],
        capture_output=True, text=True,
    )


class TemplateScriptsAreLoadable(unittest.TestCase):
    """模块顶层写坏了要当场失败，而不是变成一份空报告。"""

    def test_every_template_imports(self) -> None:
        for path in sorted(TEMPLATES.glob("*.py")):
            if path.name in IMPORT_EXEMPT:
                continue
            with self.subTest(script=path.name):
                _load(path, f"_probe_{path.stem}")

    def test_every_template_has_working_help(self) -> None:
        for path in sorted(TEMPLATES.glob("*.py")):
            if path.name in IMPORT_EXEMPT:
                continue
            with self.subTest(script=path.name):
                proc = _run(path.name, "--help")
                self.assertEqual(proc.returncode, 0,
                                 f"{path.name} --help 失败：{proc.stderr[-400:]}")
                self.assertTrue(proc.stdout.strip())


class EvidenceMapChecks(unittest.TestCase):
    HEADER = ("dataset_id,kind,claim_ids,result_ids,source_ids,actual_location,"
              "sha256,access_route,restriction,license_or_terms,generated_by,"
              "status,updated_at")

    def _workspace(self, tmp: Path, sha: str, location: str = "Data-Figures/f.csv"):
        for folder in ("Intermediate-Outputs", "Data-Figures", "Data-Scripts"):
            (tmp / folder).mkdir(parents=True, exist_ok=True)
        (tmp / "Data-Figures/f.csv").write_text("x,y\n1,2\n", encoding="utf-8")
        (tmp / "Data-Scripts/plot.py").write_text("print(1)\n", encoding="utf-8")
        (tmp / "Intermediate-Outputs/RESULTS.jsonl").write_text(
            '{"id": "R-001", "name": "n", "value": 1}\n', encoding="utf-8")
        row = (f"DS-001,figure_source,C-001,R-001,S-001,{location},{sha},"
               f"support_package,NONE,official,Data-Scripts/plot.py,VERIFIED,"
               f"2026-08-11T00:00:00+08:00")
        (tmp / "Intermediate-Outputs/SOURCE_DATA_MAP.csv").write_text(
            f"{self.HEADER}\n{row}\n", encoding="utf-8")

    def _real_sha(self, tmp: Path) -> str:
        import hashlib
        return hashlib.sha256((tmp / "Data-Figures/f.csv").read_bytes()).hexdigest()

    def test_matching_hash_passes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            (tmp / "Data-Figures").mkdir(parents=True)
            (tmp / "Data-Figures/f.csv").write_text("x,y\n1,2\n", encoding="utf-8")
            self._workspace(tmp, self._real_sha(tmp))
            proc = _run("verify_evidence_map.py", "--workspace", str(tmp))
            self.assertEqual(proc.returncode, 0, proc.stdout)

    def test_stale_hash_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            self._workspace(tmp, "0" * 64)
            proc = _run("verify_evidence_map.py", "--workspace", str(tmp))
            self.assertEqual(proc.returncode, 1)
            self.assertIn("EVIDENCE_HASH_STALE", proc.stdout)

    def test_missing_map_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            (tmp / "Intermediate-Outputs").mkdir(parents=True)
            proc = _run("verify_evidence_map.py", "--workspace", str(tmp))
            self.assertEqual(proc.returncode, 1)
            self.assertIn("EVIDENCE_MAP_MISSING", proc.stdout)


class SearchDisciplineChecks(unittest.TestCase):
    def _workspace(self, tmp: Path) -> None:
        (tmp / "Reference-Papers").mkdir(parents=True, exist_ok=True)
        (tmp / "Paper-Outputs/paper").mkdir(parents=True, exist_ok=True)
        (tmp / "Reference-Papers/SEARCH_LOG.md").write_text(
            "# 检索日志\n", encoding="utf-8")

    def test_domain_list_parses_from_rules(self) -> None:
        module = _load(TEMPLATES / "verify_search_discipline.py", "_vsd")
        domains = module.parse_forbidden_domains(module.RULES)
        self.assertIn("csdn.net", domains)
        self.assertIn("github.com", domains)

    def test_domain_in_artifact_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            self._workspace(tmp)
            (tmp / "Paper-Outputs/paper/sec_refs.tex").write_text(
                "见 https://github.com/foo/bar\n", encoding="utf-8")
            proc = _run("verify_search_discipline.py", "--workspace", str(tmp))
            self.assertEqual(proc.returncode, 1)
            self.assertIn("FORBIDDEN_DOMAIN_IN_ARTIFACT", proc.stdout)

    def test_rehearsal_mode_downgrades(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            self._workspace(tmp)
            (tmp / "Paper-Outputs/paper/sec_refs.tex").write_text(
                "见 https://github.com/foo/bar\n", encoding="utf-8")
            proc = _run("verify_search_discipline.py", "--workspace", str(tmp),
                        "--mode", "rehearsal")
            self.assertEqual(proc.returncode, 0)

    def test_logged_hit_needs_a_discard_marker(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            self._workspace(tmp)
            log = tmp / "Reference-Papers/SEARCH_LOG.md"
            log.write_text("# 检索日志\n- 命中 csdn.net/x\n", encoding="utf-8")
            self.assertIn("FORBIDDEN_DOMAIN_UNMARKED",
                          _run("verify_search_discipline.py",
                               "--workspace", str(tmp)).stdout)
            log.write_text("# 检索日志\n- 误命中 csdn.net/x，已关闭，弃用\n",
                           encoding="utf-8")
            proc = _run("verify_search_discipline.py", "--workspace", str(tmp))
            self.assertEqual(proc.returncode, 0, proc.stdout)

    def test_unparseable_rules_fail_loudly(self) -> None:
        """空清单会让每条比对都通过。必须显式失败，不能报一片绿。"""
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            self._workspace(tmp)
            empty = tmp / "empty-rules.md"
            empty.write_text("# 没有域名清单\n", encoding="utf-8")
            proc = _run("verify_search_discipline.py", "--workspace", str(tmp),
                        "--rules", str(empty))
            self.assertEqual(proc.returncode, 2)
            self.assertIn("FAIL_CONTRACT", proc.stdout)


class LedgerChecks(unittest.TestCase):
    HEADER = ("pass_id,stage,item,file_location,observed,expected_or_tolerance,"
              "evidence,checker,checked_at,status")

    def _write(self, tmp: Path, row: str) -> None:
        (tmp / "Review-Results").mkdir(parents=True, exist_ok=True)
        (tmp / "Data-Figures").mkdir(parents=True, exist_ok=True)
        (tmp / "Data-Figures/F-001.pdf").write_text("x", encoding="utf-8")
        (tmp / "Review-Results/REVIEW_PASS_ITEMS.csv").write_text(
            f"{self.HEADER}\n{row}\n", encoding="utf-8")

    def _errors(self, tmp: Path) -> list[str]:
        out = tmp / "report.json"
        _run("verify_ledgers.py", "--workspace", str(tmp), "--out", str(out))
        return json.loads(out.read_text(encoding="utf-8"))["errors"]

    def test_contracts_parse_from_templates_doc(self) -> None:
        module = _load(TEMPLATES / "verify_ledgers.py", "_vl")
        contracts = module.parse_contracts(module.TEMPLATES)
        self.assertIn("NATURE_QA.csv", contracts)
        self.assertIn("qa_id", contracts["NATURE_QA.csv"])

    def test_clean_row_has_no_errors(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            self._write(tmp, "P-001,T8,尺寸,Data-Figures/F-001.pdf,实测 170mm,"
                             "≤180mm,R-001,x,2026-08-11T00:00:00+08:00,PASS")
            self.assertEqual(self._errors(tmp), [])

    def test_missing_path_and_blank_observed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            self._write(tmp, "P-001,T8,尺寸,Data-Figures/F-404.pdf,,"
                             "≤180mm,R-001,x,2026-08-11T00:00:00+08:00,PASS")
            joined = " ".join(self._errors(tmp))
            self.assertIn("LEDGER_PATH_MISSING", joined)
            self.assertIn("LEDGER_BLANK_OBSERVED", joined)

    def test_template_placeholder_row(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            self._write(tmp, "P-001,T8,尺寸,Data-Figures/F-001.pdf,<实际观察>,"
                             "<容差>,R-001,x,2026-08-11T00:00:00+08:00,PASS")
            self.assertIn("LEDGER_PLACEHOLDER_ROW", " ".join(self._errors(tmp)))


class ProseRevisionChecks(unittest.TestCase):
    ORIGINAL = ("由式~\\eqref{eq:b} 可知，禁行时刻只占全过程的 $6.9\\%$——"
                "\\textbf{巷道进水后很快就不能走了}，残差 $15$--$198$ \\si{m}。\n")

    def _pair(self, tmp: Path, after: str) -> tuple[Path, Path]:
        before_dir, after_dir = tmp / "before", tmp / "after"
        before_dir.mkdir(parents=True, exist_ok=True)
        after_dir.mkdir(parents=True, exist_ok=True)
        (before_dir / "sec.tex").write_text(self.ORIGINAL, encoding="utf-8")
        (after_dir / "sec.tex").write_text(after, encoding="utf-8")
        return before_dir, after_dir

    def _run_pair(self, tmp: Path, after: str) -> subprocess.CompletedProcess:
        before_dir, after_dir = self._pair(tmp, after)
        return _run("verify_prose_revision.py",
                    "--before", str(before_dir), "--after", str(after_dir))

    def test_identical_revision_passes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            proc = self._run_pair(tmp, self.ORIGINAL)
            self.assertEqual(proc.returncode, 0, proc.stdout)

    def test_range_dash_turned_into_colon(self) -> None:
        """15--198 m（15 到 198 米）被改成 15:198（读作 15 比 198）。

        数字没变、LaTeX 没变，改的是占位符之间的纯文本标点——实测有 5 处这样逃过了
        段落级的四道闸。
        """
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            proc = self._run_pair(tmp, self.ORIGINAL.replace("$15$--$198$",
                                                             "$15$:$198$"))
            self.assertEqual(proc.returncode, 1)
            self.assertIn("RANGE_DASH_DRIFT", proc.stdout)

    def test_hedging_a_firm_claim(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            proc = self._run_pair(
                tmp, self.ORIGINAL.replace("很快就不能走了", "可能很快就不能走了"))
            self.assertEqual(proc.returncode, 1)
            self.assertIn("HEDGE_INFLATION", proc.stdout)

    def test_number_drift(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            proc = self._run_pair(tmp, self.ORIGINAL.replace("6.9", "7.0"))
            self.assertEqual(proc.returncode, 1)
            self.assertIn("NUMBER_DRIFT", proc.stdout)


if __name__ == "__main__":
    unittest.main()
