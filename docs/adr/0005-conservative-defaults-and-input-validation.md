# ADR-0005: Ship conservative Apple Silicon defaults and validate generation shapes

## Status

Accepted, retrospective, inferred 2026-11-09

## Context

Local video diffusion is memory-heavy, and the runtime expects specific shapes. Users need defaults that work on a laptop-class machine and early errors for invalid shapes.

## Decision

The defaults are 512x320, 65 frames, 24 fps, 8/3 distilled steps, and low-RAM block streaming on. The CLI and the GUI server both require dimensions between 128 and 1920 and divisible by 32, and frame counts of the form 8k+1. The GUI server also clamps fps (1-60), steps (1-50 / 1-20), seed (-1 to 2^31-1), and tile counts. The web form offers a smaller preset menu (up to 768x512 and 121 frames).

## Consequences

- Positive: First runs are likely to fit in memory, and invalid shapes fail before a long model load.
- Negative: Validation is duplicated in `scripts/sulphur_mlx.py` and `gui/server.py`. The server accepts much larger values than the UI offers (up to 1920 px and 385 frames), and nobody has checked that those fit in memory (A-007).

## Alternatives considered

- Passing user values straight to the runtime and relying on its errors (not done).

## Evidence

- `README.md` (CLI Defaults table; 8k + 1 note)
- `scripts/sulphur_mlx.py` (`frame_count`, `dimension`, argparse defaults)
- `gui/server.py` (`build_command`, `clamp_int`, `ensure_multiple_of_32`, `ensure_frame_count`)
- `gui/static/index.html` (select options)
- `37801d6fcb6514d963230389179c3ce302dfc69f` (only commit; current default branch)
