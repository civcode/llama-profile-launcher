# llama-profile-launcher

A tiny Python launcher for keeping `llama.cpp` / `llama-server` model profiles in a human-readable TOML file instead of large shell aliases.

It supports shared defaults, reusable profiles, per-model overrides, arbitrary extra `llama-server` arguments, and dynamic Bash completion for model names.

## Why

Instead of maintaining aliases like this:

```bash
alias my-model='llama-server -m ... --ctx-size ... --flash-attn on ...'
```

define the model once in TOML and run:

```bash
llama qwen-flash-q4-128k
```

Adding a model to the TOML file automatically adds it to Bash completion:

```text
llama qwen<TAB><TAB>
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

Show the fully resolved command:

```bash
llama --show qwen-flash-q4-128k
```

Dry-run a launch:

```bash
llama --dry-run qwen-flash-q4-128k
```

Pass additional `llama-server` arguments through unchanged:

```bash
llama qwen-flash-q4-128k --port 8081
```

Because extra arguments are appended to the configured arguments, they are also convenient for one-off `llama-server` overrides where llama.cpp accepts the later occurrence.

Use another config file:

```bash
llama --config ~/my-models.toml --list
```

or set it once with:

```bash
export LLAMA_PROFILE_CONFIG=~/my-models.toml
```

## Configuration

The configuration has three layers:

1. `[defaults.args]` — arguments shared by every model.
2. `[profiles.<name>.args]` — reusable groups of arguments.
3. `[models.<name>.args]` — model-specific overrides.

Later layers override earlier layers by flag name.

Example:

```toml
[binaries]
native = "~/workspace/llama.cpp/build/bin/llama-server"

[defaults.args]
"--host" = "127.0.0.1"
"--port" = 8080
"--parallel" = 1
"--jinja" = true

[profiles.flash.args]
"--flash-attn" = "on"
"--load-mode" = "mmap"
"--lazy-mode" = "on"

[models."my-model"]
binary = "native"
profile = "flash"
model = "~/models/model.gguf"
server_alias = "my-model"

[models."my-model".args]
"--ctx-size" = 131072
"--n-predict" = 16384
```

### Argument values

The keys under an `.args` table are passed directly to `llama-server`.

```toml
"--ctx-size" = 131072       # -> --ctx-size 131072
"--flash-attn" = "on"      # -> --flash-attn on
"--jinja" = true            # -> --jinja
"--some-disabled-flag" = false  # omitted
```

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

The checked-in `llama-models.toml` contains the profiles that motivated this project:

- `qwen-27b-120k`
- `qwen-flash-q4-128k`
- `qwen-flash-q3-96k`
- `qwen-flash-q3-128k`
- `qwen-flash-gsq-rco-iq3-128k`

Adjust the paths for your system before using them.

## Repository layout

```text
.
├── llama                 # Python launcher
├── llama-models.toml     # model/profile configuration
├── bash_completion/
│   └── llama             # dynamic Bash completion
├── bashrc.snippet        # optional convenience aliases
├── README.md
└── LICENSE
```

## License

MIT. See [`LICENSE`](LICENSE).
