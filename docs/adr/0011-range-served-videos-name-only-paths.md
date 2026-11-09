# ADR-0011: Serve videos with HTTP Range support and filename-only path resolution

## Status

Accepted, retrospective, inferred 2026-11-09

## Context

Browser `<video>` elements seek with Range requests, and the server must not expose files outside its output and static folders.

## Decision

`/video/<name>` reduces the request to `Path(name).name` under `output/gui/` and answers single `bytes=start-end` ranges with 206 Partial Content and 512 KB chunks. Requests without a Range header get the whole file with `Accept-Ranges: bytes`. `/static/<rel>` rejects absolute paths and `..` segments.

## Consequences

- Positive: In-page seeking and download work, and simple path-traversal attempts are blocked.
- Negative: Range parsing is minimal. A suffix range (`bytes=-N`) is treated as `0-N`, and multi-range or malformed headers raise an unhandled error for that request (A-006).

## Alternatives considered

- Serving outputs through `SimpleHTTPRequestHandler`'s default directory listing (not used; explicit routes only).

## Evidence

- `gui/server.py` (`handle_video`, `serve_static`)
- `gui/static/index.html` (`<video id="player">`)
- `37801d6fcb6514d963230389179c3ce302dfc69f` (only commit; current default branch)
