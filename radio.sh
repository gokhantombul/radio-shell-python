#!/usr/bin/env bash
set -euo pipefail

# Radio Shell - Terminal FM Radio Player
# Kullanım: ./radio.sh [--install | --uninstall]

resolve_script_dir() {
    local src="${BASH_SOURCE[0]}"
    while [ -h "$src" ]; do
        local dir
        dir="$(cd -P "$(dirname "$src")" && pwd)"
        src="$(readlink "$src")"
        [[ "$src" != /* ]] && src="$dir/$src"
    done
    cd -P "$(dirname "$src")" && pwd
}

SCRIPT_DIR="$(resolve_script_dir)"

# ── Install mode ──────────────────────────────────────────────────────────────
if [[ "${1:-}" == "--install" ]]; then
    if [ -w "/usr/local/bin" ]; then
        INSTALL_PATH="/usr/local/bin/radio"
    else
        INSTALL_PATH="$HOME/.local/bin/radio"
        mkdir -p "$HOME/.local/bin"
    fi
    ln -sf "$SCRIPT_DIR/radio.sh" "$INSTALL_PATH"
    echo "✔ 'radio' komutu kuruldu: $INSTALL_PATH"
    if [[ "$INSTALL_PATH" == "$HOME/.local/bin/radio" ]] && [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo "  ⚠ ~/.local/bin henüz PATH'te yok. Shell konfigürasyonunuza ekleyin:"
        echo "    Bash/Zsh : export PATH=\"\$HOME/.local/bin:\$PATH\""
        echo "    Fish     : fish_add_path ~/.local/bin"
    fi
    exit 0
fi

if [[ "${1:-}" == "--uninstall" ]]; then
    REMOVED=0
    for p in "/usr/local/bin/radio" "$HOME/.local/bin/radio"; do
        if [ -L "$p" ] && [ "$(readlink "$p")" = "$SCRIPT_DIR/radio.sh" ]; then
            rm "$p"
            echo "✔ Kaldırıldı: $p"
            REMOVED=1
        fi
    done
    [ "$REMOVED" -eq 0 ] && echo "ℹ Kurulu 'radio' bağlantısı bulunamadı."
    exit 0
fi

# ── Runtime checks ────────────────────────────────────────────────────────────
if ! command -v ffplay >/dev/null 2>&1; then
    echo "⚠ ffplay bulunamadı. Lütfen ffmpeg yükleyin."
    echo "  macOS        : brew install ffmpeg"
    echo "  Arch Linux   : sudo pacman -S ffmpeg"
    echo "  Ubuntu/Debian: sudo apt install ffmpeg"
    echo "  Fedora       : sudo dnf install ffmpeg"
    exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "⚠ python3 bulunamadı. Lütfen Python yükleyin."
    exit 1
fi

cd "$SCRIPT_DIR"

if [ ! -d "venv" ]; then
    echo "ℹ Python sanal ortamı (venv) oluşturuluyor..."
    python3 -m venv venv
    ./venv/bin/pip install -r requirements.txt -q
fi

export PYTHONPATH="$SCRIPT_DIR"
exec ./venv/bin/python3 -m src.radio.main
