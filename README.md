# llama-profile-launcher

A tiny Python launcher for keeping `llama.cpp` / `llama-server` model profiles in a human-readable TOML file instead of large shell aliases.

It supports shared defaults, composable profiles, per-model overrides, arbitrary extra `llama-server` arguments, and dynamic Bash completion for model names.

## Why

Instead of maintaining aliases like this:

```bash
alias my-model='llama-server -m ... --ctx-size ... --flash-attn on ...'
```

define reusable settings once and compose them for each model:

```toml
[models."my-model"]
profiles = ["qwen", "flash-next", "mtp"]
```

Then launch it with:

```bash
llama my-model
```

Adding a model to the TOML file automatically adds it to Bash completion:

```text
llama my<TAB><TAB>
```

## Requirements

- Linux or another Unix-like environment
- Python 3.11+ (`tomllib` is part of the standard library)
- `llama-server` builds already installed
- Bash for the included completion script

No third-party Python packages are required.

## Install

Clone the repository, then install the launcher and config:

```bash
git clone https://github.com/civcode/llama-profile-launcher.git
cd llama-profile-launcher

install -Dm755 llama ~/.local/bin/llama
install -Dm644 llama-models.toml ~/.config/llama-profile-launcher/models.toml
```

Make sure `~/.local/bin` is on your `PATH`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Edit the binary and model paths in:

```text
~/.config/llama-profile-launcher/models.toml
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

Then model names complete dynamically:

```text
llama qwen<TAB>
```

You can also copy the optional aliases from [`bashrc.snippet`](bashrc.snippet) into `~/.bashrc`.

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

```text
/home/me/workspace/llama.cpp/build/bin/llama-server \
  -m /home/me/models/model.gguf \
  --alias qwen-flash-q4-128k \
  --host 127.0.0.1 \
  --port 8080 \
  --jinja \
  --flash-attn on \
  --ctx-size 131072
```

Dry-run a launch (same output, including extra arguments):

```bash
llama --dry-run qwen-flash-q4-128k
```

Use `--one-line` for a single-line, copy-pasteable command:

```bash
llama --one-line --show qwen-flash-q4-128k
```

Both forms are valid shell input, so either can be piped into a shell or `eval`'d.

Pass additional `llama-server` arguments through unchanged:

```bash
llama qwen-flash-q4-128k --port 8081
```

Because extra arguments are appended to the configured arguments, they are also convenient for one-off `llama-server` overrides where llama.cpp accepts the later occurrence.

Everything after the model name is treated as a `llama-server` argument, so launcher flags such as `--dry-run` and `--one-line` must come *before* the model name.

Use another config file:

```bash
llama --config ~/my-models.toml --list
```

or set it once with:

```bash
export LLAMA_PROFILE_CONFIG=~/my-models.toml
```

## Configuration

The configuration is designed around four conceptual layers:

1. `[defaults.args]` — machine/server-wide settings shared by every model.
2. Family profiles such as `qwen`, `llama`, `gemma`, or `mistral`.
3. Feature/runtime profiles such as `mtp`, `flash-next`, or an offload preset.
4. `[models."<name>".args]` — model-specific tuning and final overrides.

Family and feature profiles use the same `[profiles."<name>".args]` mechanism. A model composes as many profiles as it needs with `profiles = [...]`.

Arguments are merged in this order:

```text
defaults
→ profiles[0]
→ profiles[1]
→ ...
→ model args
```

Later layers override earlier layers by flag name. This makes profile order meaningful.

### Example

```toml
[binaries]
native = "~/workspace/llama.cpp/build/bin/llama-server"

# Machine/server-wide settings.
[defaults.args]
"--host" = "127.0.0.1"
"--port" = 8080

# Model-family settings.
[profiles."qwen".args]
"--parallel" = 1
"--jinja" = true
"--temp" = 1.0
"--top-p" = 0.95
"--top-k" = 20
"--min-p" = 0.0
"--reasoning-format" = "auto"
"--reasoning" = "auto"
"--reasoning-budget" = -1

# Feature/runtime settings.
[profiles."flash-next".args]
"--load-mode" = "mmap"
"--lazy-mode" = "on"
"--flash-attn" = "on"

[profiles."mtp".args]
"--spec-type" = "draft-mtp"
"--spec-draft-n-max" = 3

[models."my-model"]
binary = "native"
profiles = ["qwen", "flash-next", "mtp"]
model = "~/models/model.gguf"
draft_model = "~/models/mtp.gguf"
server_alias = "my-model"

# Values specific to this launch configuration.
[models."my-model".args]
"--ctx-size" = 131072
"--cache-type-k" = "q8_0"
"--cache-type-v" = "q8_0"
"--fit-target" = 3584
"--n-gpu-layers" = "all"
```

Quote profile and model names (the `"<name>"` segments). Bare TOML keys cannot contain `.` or other special characters, so an unquoted `qwen-3.8-flash-next` would be split into nested tables rather than read as one name.

### Backward compatibility

Existing configurations with a single profile continue to work:

```toml
profile = "qwen"
```

This is equivalent to:

```toml
profiles = ["qwen"]
```

Do not specify both `profile` and `profiles` on the same model.

### Argument values

The keys under an `.args` table are passed directly to `llama-server`.

```toml
"--ctx-size" = 131072           # -> --ctx-size 131072
"--flash-attn" = "on"          # -> --flash-attn on
"--kv-offload" = true           # -> --kv-offload
"--no-kv-offload" = true        # -> --no-kv-offload
"--some-disabled-flag" = false  # omitted
```

`false` means "omit this flag"; it does not automatically emit an inverse `--no-*` flag.

A list repeats the same flag:

```toml
"--some-repeatable-option" = ["one", "two"]
```

becomes:

```text
--some-repeatable-option one --some-repeatable-option two
```

Keeping the actual llama.cpp option names in TOML means new llama.cpp flags usually require no launcher changes.

## Included profiles

The checked-in `llama-models.toml` demonstrates the intended structure:

- `qwen` — model-family generation settings
- `mtp` — MTP/speculative decoding settings
- `flash-next` — Flash Next runtime settings
- `no-kv-unified` — a small opt-in runtime feature

Models compose these profiles and keep context size, cache types, fit targets, batch sizes, GPU-layer choices, and exceptional overrides in their own `.args` tables.

## Tests

Run the test suite with:

```bash
python3 -m unittest discover -s tests -v
```

## Repository layout

```text
.
├── llama                 # Python launcher
├── llama-models.toml     # model/profile configuration
├── tests/
│   └── test_profiles.py  # profile composition tests
├── bash_completion/
│   └── llama             # dynamic Bash completion
├── bashrc.snippet        # optional convenience aliases
├── README.md
└── LICENSE
```

## License

MIT. See [`LICENSE`](LICENSE).
