# llama-profile-launcher

A tiny Python launcher for keeping `llama.cpp` / `llama-server` model profiles in a human-readable JSON file instead of large shell aliases.

It supports shared defaults, composable profiles, per-model overrides, arbitrary extra `llama-server` arguments, and dynamic Bash completion for model names.

## Why

Instead of maintaining aliases like this:

```bash
alias my-model='llama-server -m ... --ctx-size ... --flash-attn on ...'
```

define reusable settings once and compose them for each model:

```json
{
  "models": {
    "my-model": {
      "profiles": ["qwen", "flash-next", "mtp"]
    }
  }
}
```

Then launch it with:

```bash
llama my-model
```

Adding a model to the JSON file automatically adds it to Bash completion.

## Requirements

- Linux or another Unix-like environment
- Python 3.11+
- `llama-server` builds already installed
- Bash for the included completion script

No third-party Python packages are required.

## Install

Clone the repository, then install the launcher and config:

```bash
git clone https://github.com/civcode/llama-profile-launcher.git
cd llama-profile-launcher

install -Dm755 llama ~/.local/bin/llama
install -Dm644 llama-models.json ~/.config/llama-profile-launcher/models.json
```

Make sure `~/.local/bin` is on your `PATH`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Edit the binary and model paths in:

```text
~/.config/llama-profile-launcher/models.json
```

### Bash completion

If your system uses `bash-completion`, install the completion file:

```bash
install -Dm644 bash_completion/llama \
  ~/.local/share/bash-completion/completions/llama
```

Open a new shell, or source it directly for the current shell:

```bash
source ~/.local/share/bash-completion/completions/llama
```

## Usage

List configured models:

```bash
llama --list
```

Launch one:

```bash
llama qwen-flash-q4-128k
```

Show the fully resolved command, one argument group per line:

```bash
llama --show qwen-flash-q4-128k
```

Dry-run a launch:

```bash
llama --dry-run qwen-flash-q4-128k
```

Use `--one-line` for a single-line, copy-pasteable command:

```bash
llama --one-line --show qwen-flash-q4-128k
```

Pass additional `llama-server` arguments through unchanged:

```bash
llama qwen-flash-q4-128k --port 8081
```

Everything after the model name is treated as a `llama-server` argument, so launcher flags such as `--dry-run` and `--one-line` must come before the model name.

Use another config file:

```bash
llama --config ~/my-models.json --list
```

or set it once with:

```bash
export LLAMA_PROFILE_CONFIG=~/my-models.json
```

## Configuration

The JSON configuration is designed around four conceptual layers:

1. `defaults.args` — machine/server-wide settings shared by every model.
2. Family profiles such as `qwen`, `llama`, `gemma`, or `mistral`.
3. Feature/runtime profiles such as `mtp`, `flash-next`, or an offload preset.
4. `models.<name>.args` — model-specific tuning and final overrides.

Family and feature profiles use the same `profiles.<name>.args` mechanism. A model composes as many profiles as it needs with a `profiles` array.

Arguments are merged in this order:

```text
defaults
→ profiles[0]
→ profiles[1]
→ ...
→ model args
```

Later layers override earlier layers by flag name, so profile order is meaningful.

### Example

```json
{
  "binaries": {
    "native": "~/workspace/llama.cpp/build/bin/llama-server"
  },
  "defaults": {
    "args": {
      "--host": "127.0.0.1",
      "--port": 8080
    }
  },
  "profiles": {
    "qwen": {
      "args": {
        "--parallel": 1,
        "--jinja": true,
        "--temp": 1.0,
        "--top-p": 0.95,
        "--top-k": 20,
        "--min-p": 0.0,
        "--reasoning-format": "auto",
        "--reasoning": "auto",
        "--reasoning-budget": -1
      }
    },
    "flash-next": {
      "args": {
        "--load-mode": "mmap",
        "--lazy-mode": "on",
        "--flash-attn": "on"
      }
    },
    "mtp": {
      "args": {
        "--spec-type": "draft-mtp",
        "--spec-draft-n-max": 3
      }
    }
  },
  "models": {
    "my-model": {
      "binary": "native",
      "profiles": ["qwen", "flash-next", "mtp"],
      "model": "~/models/model.gguf",
      "draft_model": "~/models/mtp.gguf",
      "server_alias": "my-model",
      "args": {
        "--ctx-size": 131072,
        "--cache-type-k": "q8_0",
        "--cache-type-v": "q8_0",
        "--fit-target": 3584,
        "--n-gpu-layers": "all"
      }
    }
  }
}
```

This keeps each model's metadata and its model-specific arguments in one nested object while still allowing family and runtime settings to be composed independently.

### Single-profile compatibility

The singular form remains supported:

```json
{
  "profile": "qwen"
}
```

It is equivalent to:

```json
{
  "profiles": ["qwen"]
}
```

Do not specify both `profile` and `profiles` on the same model.

### Argument values

Keys under an `args` object are passed directly to `llama-server`.

```json
{
  "--ctx-size": 131072,
  "--flash-attn": "on",
  "--kv-offload": true,
  "--no-kv-offload": true,
  "--some-disabled-flag": false
}
```

The mapping is:

```text
"--ctx-size": 131072          -> --ctx-size 131072
"--flash-attn": "on"          -> --flash-attn on
"--kv-offload": true          -> --kv-offload
"--no-kv-offload": true       -> --no-kv-offload
"--some-disabled-flag": false -> omitted
```

`false` means "omit this flag"; it does not automatically emit an inverse `--no-*` flag.

An array repeats the same flag:

```json
{
  "--some-repeatable-option": ["one", "two"]
}
```

becomes:

```text
--some-repeatable-option one --some-repeatable-option two
```

Keeping the actual llama.cpp option names in JSON means new llama.cpp flags usually require no launcher changes.

## Migrating from v0.1.0 TOML

`v0.1.0` is the last TOML-based version. Current `main` uses JSON and defaults to:

```text
~/.config/llama-profile-launcher/models.json
```

Python 3.11 can convert an existing TOML config without third-party packages:

```bash
python3 -c 'import json,tomllib,sys; json.dump(tomllib.load(open(sys.argv[1],"rb")), open(sys.argv[2],"w"), indent=2); print(file=open(sys.argv[2],"a"))' \
  ~/.config/llama-profile-launcher/models.toml \
  ~/.config/llama-profile-launcher/models.json
```

Review the generated JSON, then use the new launcher normally. Standard JSON does not support comments, so TOML comments are not carried across.

## Included profiles

The checked-in `llama-models.json` demonstrates the intended structure:

- `qwen` — model-family generation settings
- `mtp` — MTP/speculative decoding settings
- `flash-next` — Flash Next runtime settings
- `no-kv-unified` — a small opt-in runtime feature

Models compose these profiles and keep context size, cache types, fit targets, batch sizes, GPU-layer choices, and exceptional overrides in their own `args` objects.

## Tests

Run the test suite with:

```bash
python3 -m unittest discover -s tests -v
```

## Repository layout

```text
.
├── llama                 # Python launcher
├── llama-models.json     # model/profile configuration
├── tests/
│   ├── test_config.py    # JSON config loading tests
│   └── test_profiles.py  # profile composition tests
├── bash_completion/
│   └── llama             # dynamic Bash completion
├── bashrc.snippet        # optional convenience aliases
├── README.md
└── LICENSE
```

## License

MIT. See [`LICENSE`](LICENSE).
