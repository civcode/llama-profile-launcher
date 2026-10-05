from __future__ import annotations

import importlib.machinery
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOADER = importlib.machinery.SourceFileLoader("llama_launcher_router", str(ROOT / "llama"))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
assert SPEC is not None
llama = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(llama)


def router_config() -> dict:
    return {
        "binaries": {
            "qwen": "/opt/llama-qwen/bin/llama-server",
            "native": "/opt/llama/bin/llama-server",
        },
        "defaults": {
            "server_args": {
                "--host": "127.0.0.1",
                "--port": 8080,
            },
            "args": {
                "--jinja": True,
                "--temp": 1,
            },
        },
        "profiles": {
            "flash": {"args": {"--flash-attn": "on"}},
            "mtp": {"args": {"--spec-type": "draft-mtp", "--spec-draft-n-max": 3}},
        },
        "routers": {
            "qwen": {
                "binary": "qwen",
                "args": {
                    "--no-models-autoload": True,
                    "--models-max": 1,
                },
            },
            "selected": {
                "binary": "qwen",
                "models": ["qwen-64k"],
            },
        },
        "models": {
            "qwen-64k": {
                "binary": "qwen",
                "profiles": ["flash"],
                "model": "/models/qwen.gguf",
                "server_alias": "legacy-alias",
                "args": {
                    "--ctx-size": 65536,
                    "--cache-type-k": "q8_0",
                    "--cache-type-v": "q8_0",
                },
            },
            "qwen-120k": {
                "binary": "qwen",
                "profiles": ["flash", "mtp"],
                "model": "/models/qwen.gguf",
                "draft_model": "/models/qwen-mtp.gguf",
                "args": {
                    "--ctx-size": 122880,
                    "--cache-type-k": "q4_0",
                    "--cache-type-v": "q4_0",
                },
            },
            "other": {
                "binary": "native",
                "model": "/models/other.gguf",
                "args": {"--ctx-size": 32768},
            },
        },
    }


class RouterTests(unittest.TestCase):
    def test_router_collects_models_using_same_binary(self) -> None:
        router = llama.resolve_router(router_config(), "qwen")
        self.assertEqual(router.model_names, ("qwen-120k", "qwen-64k"))
        self.assertEqual(router.binary_path, "/opt/llama-qwen/bin/llama-server")

    def test_router_can_select_explicit_models(self) -> None:
        router = llama.resolve_router(router_config(), "selected")
        self.assertEqual(router.model_names, ("qwen-64k",))

    def test_router_rejects_model_from_another_binary(self) -> None:
        config = router_config()
        config["routers"]["selected"]["models"] = ["other"]
        with self.assertRaisesRegex(llama.ConfigError, "uses binary"):
            llama.resolve_router(config, "selected")

    def test_preset_contains_resolved_per_model_settings(self) -> None:
        preset = llama.router_preset_text(router_config(), "qwen")

        self.assertTrue(preset.startswith("version = 1\n"))
        self.assertIn("[qwen-64k]\n", preset)
        self.assertIn("model = /models/qwen.gguf\n", preset)
        self.assertIn("ctx-size = 65536\n", preset)
        self.assertIn("cache-type-k = q8_0\n", preset)
        self.assertIn("flash-attn = on\n", preset)

        self.assertIn("[qwen-120k]\n", preset)
        self.assertIn("model-draft = /models/qwen-mtp.gguf\n", preset)
        self.assertIn("spec-type = draft-mtp\n", preset)
        self.assertIn("ctx-size = 122880\n", preset)

    def test_preset_omits_router_controlled_arguments_and_alias(self) -> None:
        preset = llama.router_preset_text(router_config(), "qwen")
        self.assertNotIn("host =", preset)
        self.assertNotIn("port =", preset)
        self.assertNotIn("alias =", preset)
        self.assertNotIn("legacy-alias", preset)

    def test_router_command_uses_server_args_and_managed_preset_path(self) -> None:
        command = llama.flatten(
            llama.router_command(
                router_config(),
                "qwen",
                Path("/tmp/qwen.models.ini"),
            )
        )

        self.assertEqual(command[0], "/opt/llama-qwen/bin/llama-server")
        self.assertEqual(
            command[1:3],
            ["--models-preset", "/tmp/qwen.models.ini"],
        )
        self.assertIn("--host", command)
        self.assertIn("127.0.0.1", command)
        self.assertIn("--port", command)
        self.assertIn("8080", command)
        self.assertIn("--no-models-autoload", command)
        self.assertIn("--models-max", command)

    def test_legacy_defaults_host_and_port_become_router_args(self) -> None:
        config = router_config()
        config["defaults"].pop("server_args")
        config["defaults"]["args"]["--host"] = "0.0.0.0"
        config["defaults"]["args"]["--port"] = 9090

        router = llama.resolve_router(config, "qwen")
        self.assertEqual(router.args["--host"], "0.0.0.0")
        self.assertEqual(router.args["--port"], 9090)

        preset = llama.router_preset_text(config, "qwen")
        self.assertNotIn("host =", preset)
        self.assertNotIn("port =", preset)

    def test_router_rejects_models_preset_override(self) -> None:
        config = router_config()
        config["routers"]["qwen"]["args"]["--models-preset"] = "/tmp/other.ini"
        with self.assertRaisesRegex(llama.ConfigError, "must not set --models-preset"):
            llama.resolve_router(config, "qwen")

    def test_router_rejects_repeated_argument_values_for_ini(self) -> None:
        config = router_config()
        config["models"]["qwen-64k"]["args"]["--some-repeatable"] = ["one", "two"]
        with self.assertRaisesRegex(llama.ConfigError, "requires a scalar"):
            llama.router_preset_text(config, "qwen")


if __name__ == "__main__":
    unittest.main()
