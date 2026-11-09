# ADR-0001: Wrap the third-party ltx-2-mlx runtime as a pinned, unvendored checkout

## Status

Accepted, retrospective, inferred 2026-11-09

## Context

The project is a local Apple Silicon launcher for Sulphur 2 video generation. The actual MLX inference code lives in an external project, `dgrauet/ltx-2-mlx`. The repo has to run that runtime without copying its code.

## Decision

`install.sh` shallow-clones `https://github.com/dgrauet/ltx-2-mlx.git` into `runtime/ltx-2-mlx/` at tag `v0.14.8`, which can be overridden with `SULPHUR_LTX_REF`. It refuses to overwrite a non-git directory and only refetches when `--update-runtime` is passed. `runtime/` is gitignored. The project only adds a wrapper (`scripts/sulphur_mlx.py`), shell entry points, and a GUI.

## Consequences

- Positive: The repo stays tiny (about 50 KB tracked). Runtime upgrades are a one-variable change, and the pinned tag makes installs repeatable.
- Negative: Behaviour depends on an external repo and tag that this project does not control. The wrapper hard-codes runtime CLI flags (`--distilled`, `--low-ram`, `--tile-*`, `--gemma`) that may drift between tags (A-002).

## Alternatives considered

- Vendoring or forking the runtime into the repo (not done; `runtime/` is gitignored).
- Installing the runtime as a PyPI dependency (`pyproject.toml` declares no runtime dependencies).

## Evidence

- `install.sh` (`RUNTIME_REPO`, `RUNTIME_REF`, clone/update logic)
- `.gitignore` (`runtime/`)
- `README.md` (Files; Runtime line)
- `37801d6fcb6514d963230389179c3ce302dfc69f` (only commit; current default branch)
