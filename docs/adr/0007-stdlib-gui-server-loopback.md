# ADR-0007: Build the GUI on a standard-library HTTP server bound to loopback

## Status

Accepted, retrospective, inferred 2026-11-09

## Context

The project wanted a browser UI without adding dependencies (the top-level `pyproject.toml` lists none).

## Decision

`gui/server.py` uses `http.server.ThreadingHTTPServer` with a custom handler and serves a vanilla HTML/CSS/JS single page from `gui/static/`. The bind address defaults to `127.0.0.1:8786` and can be changed with `SULPHUR_GUI_HOST` / `SULPHUR_GUI_PORT`. There is no authentication. The API is `GET /api/status`, `/api/history`, `/api/jobs/<id>`, `/video/<name>`, and `POST /api/generate`.

## Consequences

- Positive: The UI has no web framework or build step and starts with whatever Python is available.
- Negative: There is no auth or CSRF protection. `POST /api/generate` accepts an arbitrary local reference-image path. That is fine on loopback, but risky if someone sets `SULPHUR_GUI_HOST` to a LAN address (A-001).

## Alternatives considered

- Gradio or another UI framework (`.gitignore` lists `.gradio`, which suggests it was considered or inherited, but it is not used).

## Evidence

- `gui/server.py` (imports, `Handler`, `main`)
- `gui/static/index.html`, `gui/static/app.js`, `gui/static/styles.css`
- `.gitignore` (`.gradio`)
- `37801d6fcb6514d963230389179c3ce302dfc69f` (only commit; current default branch)
