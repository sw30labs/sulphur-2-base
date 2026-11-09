# Architecture Decision Records

Retrospective ADRs for sulphur-2-base, written 2026-11-09 from default branch `37801d6` (single "initial MLX project scaffold" commit) after a full read of every tracked file (README.md, install.sh, gui.sh, sulphur, scripts/sulphur_mlx.py, gui/server.py, gui/static/*, models/README.md, pyproject.toml, .python-version, .gitignore, output/gui/.gitignore). Format: PorterForcesAI ADR format. Open questions are in [../assumptions.md](../assumptions.md).

| ADR | Title |
|---|---|
| [0001](0001-wrap-ltx-2-mlx-runtime-pinned-tag.md) | Wrap the third-party ltx-2-mlx runtime as a pinned, unvendored checkout |
| [0002](0002-mlxbits-distilled-q4-conversion.md) | Use the MLXBits Q4 distilled MLX conversion of Sulphur 2 as the default model |
| [0003](0003-weights-not-vendored-hf-cache-default.md) | Do not vendor weights; default to the Hugging Face cache with an optional project-local copy |
| [0004](0004-uv-and-single-installer-apple-silicon-gate.md) | Use uv and a single install.sh gated to Apple Silicon macOS |
| [0005](0005-conservative-defaults-and-input-validation.md) | Ship conservative Apple Silicon defaults and validate generation shapes |
| [0006](0006-layered-entrypoints-subprocess-argv.md) | Layer bash entry points over a Python wrapper that shells out with argv lists |
| [0007](0007-stdlib-gui-server-loopback.md) | Build the GUI on a standard-library HTTP server bound to loopback |
| [0008](0008-single-job-in-memory-polling.md) | Allow one generation at a time, tracked in memory and polled by the browser |
| [0009](0009-filesystem-outputs-with-json-sidecars.md) | Use output MP4s plus JSON sidecars on disk as the render history |
| [0010](0010-gemma-enhancer-in-gui-sulphur-enhancer-manual.md) | Use the runtime's Gemma prompt enhancer in the app; leave the Sulphur enhancer as a manual download |
| [0011](0011-range-served-videos-name-only-paths.md) | Serve videos with HTTP Range support and filename-only path resolution |
