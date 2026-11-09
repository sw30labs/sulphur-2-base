# ADR-0004: Use uv and a single install.sh gated to Apple Silicon macOS

## Status

Accepted, retrospective, inferred 2026-11-09

## Context

MLX is Metal-backed and only runs on Apple Silicon. The runtime brings its own Python project, and the launcher needs a repeatable setup path.

## Decision

`install.sh` stops unless `uname` reports `Darwin/arm64`. It requires git and curl, warns if ffmpeg is missing, and installs `uv` with the official installer (`curl | sh`) after an interactive prompt that `-y` skips. It runs `uv sync` in the runtime checkout and adds `huggingface-hub[hf_xet]`. The wrapper runs the runtime through `uv run ltx-2-mlx`. The top-level `pyproject.toml` declares no runtime dependencies (only `ruff` as a dev group) and targets Python 3.11 (`.python-version`).

## Consequences

- Positive: It's one command to get ready, the platform mismatch fails fast, and the runtime's dependencies stay isolated in its own venv.
- Negative: Piping a remote installer into `sh` is a trust decision, and `-y` skips the prompt. Linux/Intel users get a hard stop with no fallback.

## Alternatives considered

- pip/venv-based setup (not used).
- Homebrew-only installation of uv (the script uses the official installer and points to the GitHub page).

## Evidence

- `install.sh` (platform gate, uv install, `uv sync`)
- `pyproject.toml`
- `.python-version`
- `scripts/sulphur_mlx.py` (`require_runtime`, `uv run` command)
- `37801d6fcb6514d963230389179c3ce302dfc69f` (only commit; current default branch)
