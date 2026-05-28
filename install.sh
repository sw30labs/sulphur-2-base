#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_DIR="$ROOT/runtime/ltx-2-mlx"
MODEL_DIR="$ROOT/models/sulphur-2-distill-mlx-q4"
PROMPT_MODEL_DIR="$ROOT/models/sulphur-promptenhancer-mlx-q8"
RUNTIME_REPO="https://github.com/dgrauet/ltx-2-mlx.git"
RUNTIME_REF="${SULPHUR_LTX_REF:-v0.14.8}"

YES=0
DOWNLOAD_MODEL=0
DOWNLOAD_PROMPT=0
UPDATE_RUNTIME=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    -y|--yes)
      YES=1
      ;;
    --download-model)
      DOWNLOAD_MODEL=1
      ;;
    --download-prompt-enhancer)
      DOWNLOAD_PROMPT=1
      ;;
    --update-runtime)
      UPDATE_RUNTIME=1
      ;;
    -h|--help)
      cat <<'EOF'
Usage: ./install.sh [options]

Options:
  -y, --yes                    Do not prompt before installing uv.
  --download-model             Download MLXBits/sulphur-2-distill-mlx-q4 locally.
  --download-prompt-enhancer   Download MLXBits/sulphur-promptenhancer-mlx-q8 locally.
  --update-runtime             Pull/update runtime checkout before syncing.
  -h, --help                   Show this help.
EOF
      exit 0
      ;;
    *)
      printf 'Unknown option: %s\n' "$1" >&2
      exit 2
      ;;
  esac
  shift
done

if [[ -t 1 ]]; then
  BOLD=$'\033[1m'; GREEN=$'\033[1;32m'; CYAN=$'\033[1;36m'; YELLOW=$'\033[1;33m'; RED=$'\033[1;31m'; RESET=$'\033[0m'
else
  BOLD=""; GREEN=""; CYAN=""; YELLOW=""; RED=""; RESET=""
fi

step() { printf '\n%s=>%s %s\n' "$CYAN" "$RESET" "$1"; }
ok() { printf '  %sok%s %s\n' "$GREEN" "$RESET" "$1"; }
warn() { printf '  %swarn%s %s\n' "$YELLOW" "$RESET" "$1" >&2; }
fail() { printf '\n%serror%s %s\n' "$RED" "$RESET" "$1" >&2; exit 1; }

export PATH="${XDG_BIN_HOME:-$HOME/.local/bin}:$HOME/.local/bin:$PATH"

OS="$(uname -s)"
ARCH="$(uname -m)"
if [[ "$OS" != "Darwin" || "$ARCH" != "arm64" ]]; then
  fail "Sulphur MLX generation requires Apple Silicon macOS. Detected $OS/$ARCH."
fi
ok "platform: $OS/$ARCH"

for tool in git curl; do
  command -v "$tool" >/dev/null 2>&1 || fail "$tool is required."
done
ok "git + curl present"

if ! command -v ffmpeg >/dev/null 2>&1; then
  warn "ffmpeg was not found. Install it with: brew install ffmpeg"
else
  ok "ffmpeg present"
fi

if ! command -v uv >/dev/null 2>&1; then
  step "uv is not installed"
  if [[ "$YES" -ne 1 ]]; then
    read -r -p "Install uv with the official installer? [y/N] " reply
    case "$reply" in
      y|Y|yes|YES) ;;
      *) fail "uv is required. Install from https://github.com/astral-sh/uv and rerun." ;;
    esac
  fi
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="${XDG_BIN_HOME:-$HOME/.local/bin}:$HOME/.local/bin:$PATH"
fi
ok "uv present: $(uv --version)"

mkdir -p "$ROOT/runtime" "$ROOT/models" "$ROOT/output/gui"

if [[ -d "$RUNTIME_DIR/.git" ]]; then
  if [[ "$UPDATE_RUNTIME" -eq 1 ]]; then
    step "Updating runtime checkout"
    git -C "$RUNTIME_DIR" fetch --tags --depth=1 origin "$RUNTIME_REF"
    git -C "$RUNTIME_DIR" checkout --detach "FETCH_HEAD"
  else
    ok "runtime checkout already exists"
  fi
elif [[ -e "$RUNTIME_DIR" ]]; then
  fail "$RUNTIME_DIR exists but is not a git checkout."
else
  step "Cloning ltx-2-mlx runtime ($RUNTIME_REF)"
  git clone --depth=1 --branch "$RUNTIME_REF" "$RUNTIME_REPO" "$RUNTIME_DIR"
fi

step "Syncing runtime dependencies"
cd "$RUNTIME_DIR"
uv sync
uv pip install "huggingface-hub[hf_xet]"
ok "runtime ready"

if [[ "$DOWNLOAD_MODEL" -eq 1 ]]; then
  step "Downloading Sulphur MLX Q4 model"
  "$RUNTIME_DIR/.venv/bin/huggingface-cli" download \
    --local-dir "$MODEL_DIR" \
    MLXBits/sulphur-2-distill-mlx-q4
  ok "model downloaded to $MODEL_DIR"
fi

if [[ "$DOWNLOAD_PROMPT" -eq 1 ]]; then
  step "Downloading Sulphur prompt enhancer"
  "$RUNTIME_DIR/.venv/bin/huggingface-cli" download \
    --local-dir "$PROMPT_MODEL_DIR" \
    MLXBits/sulphur-promptenhancer-mlx-q8
  ok "prompt enhancer downloaded to $PROMPT_MODEL_DIR"
fi

printf '\n%sReady.%s Try:\n' "$BOLD" "$RESET"
printf '  ./gui.sh\n'
printf '  ./sulphur --prompt "A cinematic neon street market at night, rain, slow dolly forward" --frames 65\n'
