import hashlib
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LITERATURE = ROOT / "skills/mcm-gold/references/literature-library.md"
DOI_RE = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Z0-9]+$", re.IGNORECASE)


class LiteratureLibraryTests(unittest.TestCase):
    def test_bibliography_rows_are_not_truncated(self) -> None:
        text = LITERATURE.read_text(encoding="utf-8")
        bibliography = text.split("## 本地全文清单", 1)[0]
        self.assertNotIn("…", bibliography)

    def test_doi_cells_are_machine_resolvable(self) -> None:
        text = LITERATURE.read_text(encoding="utf-8")
        bibliography = text.split("## 本地全文清单", 1)[0]
        for line_number, line in enumerate(bibliography.splitlines(), start=1):
            if not line.startswith("|") or "`10." not in line:
                continue
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            doi = cells[-2].strip("`")
            self.assertRegex(doi, DOI_RE, f"line {line_number}: {doi}")


class RepositoryIntegrityTests(unittest.TestCase):
    def test_group_validator_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "tooling/validate_skill_group.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_manifest_matches_tracked_files(self) -> None:
        listed: set[str] = set()
        for line in (ROOT / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
            expected, relative = line.split("  ", 1)
            listed.add(relative)
            actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, relative)
        # Linked worktrees store .git as a pointer file rather than a directory.
        if (ROOT / ".git").exists():
            result = subprocess.run(
                ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            )
            expected_files = {
                item for item in result.stdout.splitlines() if item != "MANIFEST.sha256"
            }
        else:
            expected_files = {
                path.relative_to(ROOT).as_posix()
                for path in ROOT.rglob("*")
                if path.is_file()
                and path.name not in {"MANIFEST.sha256", ".DS_Store"}
                and path.suffix != ".pyc"
                and "__pycache__" not in path.parts
            }
        self.assertEqual(listed, expected_files)

    def test_third_party_snapshots_are_excluded_from_mit_notice(self) -> None:
        notice = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
        self.assertIn("sources/official/2026/", notice)
        self.assertIn("not covered", notice)

    def test_trigger_eval_matrix_covers_every_skill(self) -> None:
        cases = json.loads((ROOT / "tests/trigger_cases.json").read_text(encoding="utf-8"))
        expected = {path.parent.name for path in (ROOT / "skills").glob("*/SKILL.md")}
        self.assertEqual({case["target"] for case in cases}, expected)
        self.assertTrue(all(case["prompt"].strip() for case in cases))


if __name__ == "__main__":
    unittest.main()
