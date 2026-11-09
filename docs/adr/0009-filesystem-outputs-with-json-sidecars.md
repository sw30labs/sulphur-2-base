# ADR-0009: Use output MP4s plus JSON sidecars on disk as the render history

## Status

Accepted, retrospective, inferred 2026-11-09

## Context

Users want to browse and reuse past renders and their settings without running a database.

## Decision

GUI renders go to `output/gui/<epoch>_<job8>_<slug>.mp4`. CLI renders default to `output/<epoch>_<slug>.mp4`. After a successful run, the wrapper writes `<name>.json` next to the MP4 with the prompt, model, shape, steps, seed, flags, wall time, and full command. `/api/history` lists the newest MP4s by mtime and reads sidecars for display. `output/*` is gitignored, and `output/gui/.gitignore` keeps the directory present.

## Consequences

- Positive: History survives restarts and can be inspected with ordinary tools, and every render records how it was produced.
- Negative: Sidecars are only written on success, so failed runs leave no record. History is a directory scan with no index.

## Alternatives considered

- SQLite or another database for history (not used).

## Evidence

- `scripts/sulphur_mlx.py` (`resolve_out`, `write_sidecar`)
- `gui/server.py` (`OUTPUT`, `list_outputs`, `build_command` filename)
- `.gitignore`; `output/gui/.gitignore`
- `37801d6fcb6514d963230389179c3ce302dfc69f` (only commit; current default branch)
