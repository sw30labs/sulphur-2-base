# ADR-0003: Do not vendor weights; default to the Hugging Face cache with an optional project-local copy

## Status

Accepted, retrospective, inferred 2026-11-09

## Context

The model bundle is tens of gigabytes. It cannot live in git, and users may already have it in their Hugging Face cache.

## Decision

By default the wrapper passes the Hub repo ID to the runtime, which downloads into the Hugging Face cache on first use. `install.sh --download-model` (and `--download-prompt-enhancer`) puts copies under `models/` via `huggingface-cli`. `default_model()` automatically prefers `models/sulphur-2-distill-mlx-q4/` when its `config.json` exists. `models/*` is gitignored except `models/README.md`.

## Consequences

- Positive: There are no large files in git, existing caches get reused, and a project-local copy is opt-in and picked up automatically.
- Negative: The first generation can block on a very large download. Two copies (cache plus `models/`) can exist at once.

## Alternatives considered

- Always downloading into `models/` during install (offered only behind a flag).

## Evidence

- `scripts/sulphur_mlx.py` (`LOCAL_MODEL`, `default_model`)
- `install.sh` (`--download-model`, `--download-prompt-enhancer`)
- `models/README.md`
- `.gitignore` (`models/*`, `!models/README.md`)
- `37801d6fcb6514d963230389179c3ce302dfc69f` (only commit; current default branch)
