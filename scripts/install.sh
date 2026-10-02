#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
HOST="${1:-workstation}"
CONFIG="$ROOT/config/hosts/$HOST.json"

if [[ ! -f "$CONFIG" ]]; then
    echo "install: host config not found: $CONFIG" >&2
    exit 1
fi

install -Dm755 "$ROOT/llama" "$HOME/.local/bin/llama"
install -Dm644 "$ROOT/shell/bash_completion/llama" \
    "$HOME/.local/share/bash-completion/completions/llama"

mkdir -p "$HOME/.config/llama-profile-launcher"
ln -sfn "$CONFIG" "$HOME/.config/llama-profile-launcher/models.json"

echo "Installed llama-profile-launcher"
echo "Config: $CONFIG"
echo "Linked: $HOME/.config/llama-profile-launcher/models.json"
