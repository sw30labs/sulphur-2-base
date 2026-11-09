# ADR-0006: Layer bash entry points over a Python wrapper that shells out with argv lists

## Status

Accepted, retrospective, inferred 2026-11-09

## Context

Users run generations from a terminal and from a browser. Both paths need the same command construction, and prompts are untrusted free text.

## Decision

`./sulphur` execs `scripts/sulphur_mlx.py`, the self-described "safe command builder". That script assembles an argv list and runs it with `subprocess.Popen` (no shell), with `cwd` set to the runtime and output streamed. The GUI server does not call the runtime directly. It builds an argv list for the same wrapper script with `sys.executable`. On success the wrapper writes a JSON sidecar.

## Consequences

- Positive: There is one code path for generation. Prompts are passed as single argv elements, so there is no shell-injection surface. The terminal and GUI logs match.
- Negative: Every GUI generation adds an extra Python process hop. `./sulphur` prefers the system `python3` while `gui.sh` prefers the runtime venv Python, which is inconsistent but harmless because the wrapper only uses the standard library (A-009).

## Alternatives considered

- Importing the runtime as a library in-process (not done).
- Building a shell string (avoided; argv lists throughout).

## Evidence

- `sulphur`
- `gui.sh`
- `scripts/sulphur_mlx.py` (module docstring, `stream_command`, `main`)
- `gui/server.py` (`build_command`, `run_job`)
- `37801d6fcb6514d963230389179c3ce302dfc69f` (only commit; current default branch)
