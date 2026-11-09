# ADR-0002: Use the MLXBits Q4 distilled MLX conversion of Sulphur 2 as the default model

## Status

Accepted, retrospective, inferred 2026-11-09

## Context

The upstream SulphurAI/Sulphur-2-base release is Diffusers/GGUF and cannot run directly on the MLX runtime. The README says the MLX path uses a third-party conversion.

## Decision

The default model is `MLXBits/sulphur-2-distill-mlx-q4`, run with `ltx-2-mlx generate --distilled`, with separate stage 1 and stage 2 step counts (8 and 3 by default). The text encoder defaults to `mlx-community/gemma-3-12b-it-4bit`. `--model` and `--gemma` override both.

## Consequences

- Positive: Sulphur 2 runs natively on Apple Silicon with a 4-bit, few-step distilled pipeline sized for local memory.
- Negative: Output quality and fidelity depend on a third-party conversion whose equivalence to the base model is asserted, not shown (A-003). The Q4 bundle is still about 34 GB (A-004).

## Alternatives considered

- Running the original Diffusers/GGUF release (README says it is the upstream format; not used).
- A non-distilled pipeline (no flag or option for it in the wrapper).

## Evidence

- `scripts/sulphur_mlx.py` (`DEFAULT_MODEL`, `DEFAULT_GEMMA`, `--distilled` command)
- `README.md` (intro; CLI Defaults; Notes)
- `pyproject.toml` (description)
- `37801d6fcb6514d963230389179c3ce302dfc69f` (only commit; current default branch)
