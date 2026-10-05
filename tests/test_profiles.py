from __future__ import annotations

import importlib.machinery
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOADER = importlib.machinery.SourceFileLoader("llama_launcher", str(ROOT / "llama"))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
assert SPEC is not None
llama = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(llama)


def base_config() -> dict:
    return {
        "binaries": {"test": "/bin/llama-server"},
        "defaults": {"args": {"--shared": "default", "--host": "127.0.0.1"}},
        "profiles": {
            "family": {"args": {"--shared": "family", "--family": True}},
            "runtime": {"args": {"--shared": "runtime", "--runtime": "on"}},
        },
        "models": {
            "test": {
                "binary": "test",
                "model": "/models/test.gguf",
                "profiles": ["family", "runtime"],
                "args": {"--shared": "model", "--ctx-size": 4096},
            }
        },
    }


class ProfileTests(unittest.TestCase):
    def test_resolve_model_returns_normalized_model_data(self) -> None:
        config = base_config()
        config["models"]["test"]["draft_model"] = "~/models/draft.gguf"
        config["models"]["test"]["server_alias"] = "test-alias"

        resolved = llama.resolve_model(config, "test")

        self.assertEqual(resolved.name, "test")
        self.assertEqual(resolved.binary_key, "test")
        self.assertEqual(resolved.binary_path, "/bin/llama-server")
        self.assertEqual(resolved.model_path, "/models/test.gguf")
        self.assertTrue(resolved.draft_model_path.endswith("/models/draft.gguf"))
        self.assertEqual(resolved.server_alias, "test-alias")
        self.assertEqual(resolved.args["--shared"], "model")
        self.assertEqual(resolved.args["--runtime"], "on")
        self.assertEqual(resolved.args["--ctx-size"], 4096)

    def test_model_command_uses_resolved_model(self) -> None:
        config = base_config()
        config["models"]["test"]["draft_model"] = "/models/draft.gguf"
        config["models"]["test"]["server_alias"] = "test-alias"

        command = llama.flatten(llama.model_command(config, "test"))

        self.assertEqual(command[0], "/bin/llama-server")
        self.assertEqual(command[1:3], ["-m", "/models/test.gguf"])
        self.assertIn("-md", command)
        self.assertIn("/models/draft.gguf", command)
        self.assertIn("--alias", command)
        self.assertIn("test-alias", command)

    def test_profiles_are_composed_in_order_then_model_overrides(self) -> None:
        command = llama.flatten(llama.model_command(base_config(), "test"))
        self.assertEqual(command.count("--shared"), 1)
        shared = command.index("--shared")
        self.assertEqual(command[shared + 1], "model")
        self.assertIn("--family", command)
        self.assertIn("--runtime", command)
        self.assertIn("--host", command)
        self.assertIn("--ctx-size", command)

    def test_later_profile_overrides_earlier_profile(self) -> None:
        config = base_config()
        config["models"]["test"]["args"].pop("--shared")
        command = llama.flatten(llama.model_command(config, "test"))
        shared = command.index("--shared")
        self.assertEqual(command[shared + 1], "runtime")

    def test_legacy_singular_profile_is_supported(self) -> None:
        config = base_config()
        config["models"]["test"].pop("profiles")
        config["models"]["test"]["profile"] = "family"
        command = llama.flatten(llama.model_command(config, "test"))
        self.assertIn("--family", command)
        self.assertNotIn("--runtime", command)

    def test_profile_and_profiles_are_mutually_exclusive(self) -> None:
        config = base_config()
        config["models"]["test"]["profile"] = "family"
        with self.assertRaisesRegex(llama.ConfigError, "cannot use both"):
            llama.model_command(config, "test")

    def test_profiles_must_be_a_list_of_names(self) -> None:
        config = base_config()
        config["models"]["test"]["profiles"] = "family"
        with self.assertRaisesRegex(llama.ConfigError, "must be a list of names"):
            llama.model_command(config, "test")

    def test_unknown_profile_is_reported(self) -> None:
        config = base_config()
        config["models"]["test"]["profiles"] = ["family", "missing"]
        with self.assertRaisesRegex(llama.ConfigError, "unknown profile 'missing'"):
            llama.model_command(config, "test")


if __name__ == "__main__":
    unittest.main()
