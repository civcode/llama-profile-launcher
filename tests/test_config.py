from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOADER = importlib.machinery.SourceFileLoader("llama_launcher_config", str(ROOT / "llama"))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
assert SPEC is not None
llama = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(llama)


class ConfigTests(unittest.TestCase):
    def write_config(self, value) -> Path:
        handle = tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".json", delete=False
        )
        with handle:
            json.dump(value, handle)
        return Path(handle.name)

    def test_default_config_is_json(self) -> None:
        self.assertEqual(llama.DEFAULT_CONFIG.name, "models.json")

    def test_loads_json_config(self) -> None:
        path = self.write_config(
            {
                "binaries": {"test": "/bin/llama-server"},
                "models": {
                    "test": {
                        "binary": "test",
                        "model": "/models/test.gguf",
                        "args": {"--jinja": True},
                    }
                },
            }
        )
        try:
            config = llama.load_config(path)
            self.assertTrue(config["models"]["test"]["args"]["--jinja"])
        finally:
            path.unlink()

    def test_invalid_json_is_reported(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".json", delete=False
        ) as handle:
            handle.write('{"binaries": ')
            path = Path(handle.name)
        try:
            with self.assertRaisesRegex(llama.ConfigError, "invalid JSON"):
                llama.load_config(path)
        finally:
            path.unlink()


if __name__ == "__main__":
    unittest.main()
