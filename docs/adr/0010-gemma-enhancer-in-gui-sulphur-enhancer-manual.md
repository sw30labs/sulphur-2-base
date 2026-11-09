# ADR-0010: Use the runtime's Gemma prompt enhancer in the app; leave the Sulphur enhancer as a manual download

## Status

Accepted, retrospective, inferred 2026-11-09

## Context

Sulphur publishes a dedicated prompt-enhancer model. The ltx-2-mlx runtime ships its own Gemma-based `--enhance-prompt`.

## Decision

The GUI's Enhance checkbox and the CLI's `--enhance-prompt` pass through to the runtime's Gemma enhancer. `MLXBits/sulphur-promptenhancer-mlx-q8` (about 10 GB) can be downloaded with `install.sh --download-prompt-enhancer`, but nothing in the code loads it. The README calls it a manual / LM Studio-style workflow.

## Consequences

- Positive: Enhancement works with no extra model download beyond the text encoder that is already needed.
- Negative: The model-specific enhancer is not wired in. A user who downloads it gets no in-app benefit.

## Alternatives considered

- Wiring the Sulphur enhancer into the pipeline (not implemented).

## Evidence

- `README.md` (Download Weights Up Front)
- `install.sh` (`--download-prompt-enhancer`)
- `scripts/sulphur_mlx.py` (`--enhance-prompt`)
- `gui/server.py` (`enhance_prompt`)
- `37801d6fcb6514d963230389179c3ce302dfc69f` (only commit; current default branch)
