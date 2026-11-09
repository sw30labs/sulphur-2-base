# ADR-0008: Allow one generation at a time, tracked in memory and polled by the browser

## Status

Accepted, retrospective, inferred 2026-11-09

## Context

Only one video generation can realistically run on a single machine at a time, and the UI needs progress feedback.

## Decision

The server keeps a process-local `jobs` dict and one `active_job_id` under a lock. A second `POST /api/generate` gets HTTP 409. Each job runs in a daemon thread, and its log is ANSI-stripped and capped at 700 lines. The browser polls `/api/jobs/<id>` every second. On page load, `/api/status` reattaches to an already running job.

## Consequences

- Positive: This avoids GPU/memory contention, and the implementation is simple with no queue or database.
- Negative: Job state is lost on restart. Only finished MP4s and sidecars persist (see ADR-0009). The module docstring says status is "streamed", but it is actually polled.

## Alternatives considered

- A job queue allowing several queued generations (not implemented).
- Server-sent events or WebSockets for progress (not used; polling).

## Evidence

- `gui/server.py` (`jobs`, `active_job_id`, `handle_generate` 409, `append_log`, `run_job`)
- `gui/static/app.js` (`pollJob`, `setTimeout(pollJob, 1000)`, `loadStatus`)
- `37801d6fcb6514d963230389179c3ce302dfc69f` (only commit; current default branch)
