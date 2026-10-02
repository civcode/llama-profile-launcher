# llama-profile-launcher

A tiny Python launcher for keeping `llama.cpp` / `llama-server` model profiles in JSON instead of large shell aliases.

The repository can also be the source of truth for a machine's actual llama.cpp setup: launcher code, host configs, shell integration, and install scripts live together, while GGUFs and llama.cpp builds stay outside the repo.

## Repository layout

```text
.
├── llama
├── config/
│   ├── examples/
│   │   └── models.example.json
│   └── hosts/
│       └── workstation.json
├── shell/
│   ├── bash_completion/
│   │   └── llama
│   └── bashrc.snippet
├── scripts/
│   └── install.sh
├── tests/
│   ├── test_config.py
│   └── test_profiles.py
├── README.md
├── LICENSE
└── .gitignore
```

`config/examples/models.example.json` is the portable example configuration. `config/hosts/workstation.json` is the checked-in configuration for the actual workstation.

## Install this workstation setup

Clone the repository and run:

```bash
git clone https://github.com/civcode/llama-profile-launcher.git
cd llama-profile-launcher
./scripts/install.sh workstation
```

The installer:

- installs `llama` to `~/.local/bin/llama`
- installs Bash completion
- symlinks `config/hosts/workstation.json` to `~/.config/llama-profile-launcher/models.json`

The symlink keeps the repository configuration as the source of truth. Editing and committing `config/hosts/workstation.json` immediately changes the configuration used by the launcher.

For another machine, add another file under `config/hosts/` and pass its basename:

```bash
./scripts/install.sh laptop
```

which uses `config/hosts/laptop.json`.

Make sure `~/.local/bin` is on `PATH`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Optional convenience aliases are in `shell/bashrc.snippet`.

## Usage

List configured models:

```bash
llama --list
```

Launch a model:

```bash
llama qwen-27b-120k
```

Show the fully resolved command:

```bash
llama --show qwen-27b-120k
```

Dry-run a launch:

```bash
llama --dry-run qwen-27b-120k
```

Use another config explicitly:

```bash
llama --config ./config/examples/models.example.json --list
```

Everything after the model name is passed to `llama-server`, so launcher flags such as `--dry-run` and `--one-line` must come before the model name.

## Configuration model

Configuration is layered as:

```text
defaults
→ profiles[0]
→ profiles[1]
→ ...
→ model args
```

Later layers override earlier layers by flag name.

A model can compose family and feature/runtime profiles:

```json
{
  "profiles": ["qwen-base", "flash-attn", "mtp"]
}
```

Typical responsibilities are:

```text
defaults
    machine/server-wide settings
    host, port

family profiles
    qwen-base
    llama
    gemma
    mistral

feature/runtime profiles
    mtp
    flash-attn
    flash-next
    no-kv-unified

model args
    ctx-size
    cache types
    fit-target
    batch sizes
    GPU layers
    exceptional overrides
```

The singular legacy form `"profile": "name"` is still accepted. Do not specify both `profile` and `profiles` for the same model.

## Argument values

Keys inside an `args` object are passed directly to `llama-server`:

```json
{
  "--ctx-size": 131072,
  "--flash-attn": "on",
  "--kv-offload": true,
  "--some-disabled-flag": false
}
```

This becomes:

```text
--ctx-size 131072
--flash-attn on
--kv-offload
```

A boolean `false` omits the flag; it does not automatically emit an inverse `--no-*` option.

JSON arrays repeat a flag:

```json
{
  "--some-repeatable-option": ["one", "two"]
}
```

## Data vs. artifacts

Keep this repository declarative. Store model paths and build paths here, but keep the large artifacts themselves elsewhere:

```text
~/models/
    GGUF files

~/workspace/llama.cpp*
    llama.cpp source/builds

llama-profile-launcher/
    launcher
    configuration
    shell integration
    setup scripts
    tests
```

## Tests

```bash
python3 -m unittest discover -s tests -v
```

No third-party Python packages are required.

## Migration from v0.1.0

`v0.1.0` is the last TOML-based release. Current `main` uses strict JSON and defaults to:

```text
~/.config/llama-profile-launcher/models.json
```

Standard JSON does not support comments.

## License

MIT. See [`LICENSE`](LICENSE).
