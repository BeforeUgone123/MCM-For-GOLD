import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INITIALIZER = ROOT / "skills/mcm-gold/templates/init_result_workspace.py"


def load_initializer():
    spec = importlib.util.spec_from_file_location("init_result_workspace", INITIALIZER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载 {INITIALIZER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


if __name__ == "__main__":
    unittest.main()
