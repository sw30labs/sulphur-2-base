"""Sulphur 2 MLX GUI.

Tiny stdlib server that shells out to scripts/sulphur_mlx.py and streams
generation status to a single-page browser UI.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parent.parent
STATIC = Path(__file__).resolve().parent / "static"
OUTPUT = ROOT / "output" / "gui"
SCRIPT = ROOT / "scripts" / "sulphur_mlx.py"
RUNTIME = ROOT / "runtime" / "ltx-2-mlx"

jobs_lock = threading.Lock()
jobs: dict[str, "Job"] = {}
active_job_id: str | None = None


@dataclass
class Job:
    id: str
    status: str
    created_at: float
    command: list[str]
    prompt: str
    out_file: str
    params: dict[str, Any] = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)
    exit_code: int | None = None
    duration: float | None = None
    error: str | None = None

    def public(self) -> dict[str, Any]:
        data = asdict(self)
        data["video_url"] = f"/video/{Path(self.out_file).name}" if self.status == "done" else None
        data["filename"] = Path(self.out_file).name
        return data


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug[:48] or "sulphur"


def json_response(handler: SimpleHTTPRequestHandler, payload: Any, status: int = 200) -> None:
    body = json.dumps(payload, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def read_json(handler: SimpleHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0"))
    raw = handler.rfile.read(length) if length else b"{}"
    try:
        data = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object.")
    return data


def clamp_int(data: dict[str, Any], key: str, default: int, low: int, high: int) -> int:
    try:
        value = int(data.get(key, default))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be an integer.") from exc
    if value < low or value > high:
        raise ValueError(f"{key} must be between {low} and {high}.")
    return value


def clamp_float(data: dict[str, Any], key: str, default: float, low: float, high: float) -> float:
    try:
        value = float(data.get(key, default))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be a number.") from exc
    if value < low or value > high:
        raise ValueError(f"{key} must be between {low} and {high}.")
    return value


def ensure_multiple_of_32(value: int, name: str) -> None:
    if value % 32 != 0:
        raise ValueError(f"{name} must be divisible by 32.")


def ensure_frame_count(value: int) -> None:
    if (value - 1) % 8 != 0:
        raise ValueError("frames must satisfy 8k + 1.")


def build_command(data: dict[str, Any], job_id: str) -> tuple[list[str], Path, str]:
    prompt = str(data.get("prompt", "")).strip()
    if not prompt:
        raise ValueError("Prompt is required.")

    width = clamp_int(data, "width", 512, 128, 1920)
    height = clamp_int(data, "height", 320, 128, 1920)
    frames = clamp_int(data, "frames", 65, 9, 385)
    ensure_multiple_of_32(width, "width")
    ensure_multiple_of_32(height, "height")
    ensure_frame_count(frames)

    frame_rate = clamp_float(data, "frame_rate", 24.0, 1.0, 60.0)
    stage1_steps = clamp_int(data, "stage1_steps", 8, 1, 50)
    stage2_steps = clamp_int(data, "stage2_steps", 3, 1, 20)
    seed = clamp_int(data, "seed", -1, -1, 2**31 - 1)
    tile_frames = clamp_int(data, "tile_frames", 1, 1, 8)
    tile_spatial = clamp_int(data, "tile_spatial", 1, 1, 4)

    image = str(data.get("image", "")).strip()
    if image:
        image_path = Path(image).expanduser()
        if not image_path.exists():
            raise ValueError(f"Image path not found: {image_path}")
        image = str(image_path)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    filename = f"{int(time.time())}_{job_id[:8]}_{slugify(prompt)}.mp4"
    out_path = OUTPUT / filename

    command = [
        sys.executable,
        str(SCRIPT),
        "--prompt",
        prompt,
        "--out",
        str(out_path),
        "--width",
        str(width),
        "--height",
        str(height),
        "--frames",
        str(frames),
        "--frame-rate",
        f"{frame_rate:g}",
        "--stage1-steps",
        str(stage1_steps),
        "--stage2-steps",
        str(stage2_steps),
        "--seed",
        str(seed),
        "--tile-frames",
        str(tile_frames),
        "--tile-spatial",
        str(tile_spatial),
    ]
    if image:
        command.extend(["--image", image])
    if not bool(data.get("low_ram", True)):
        command.append("--no-low-ram")
    if bool(data.get("enhance_prompt", False)):
        command.append("--enhance-prompt")
    return command, out_path, prompt


def append_log(job: Job, line: str) -> None:
    clean = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", line.rstrip())
    with jobs_lock:
        job.logs.append(clean)
        if len(job.logs) > 700:
            job.logs = job.logs[-700:]


def run_job(job_id: str) -> None:
    global active_job_id
    with jobs_lock:
        job = jobs[job_id]
        job.status = "running"
        start = time.time()

    try:
        proc = subprocess.Popen(
            job.command,
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            append_log(job, line)
        code = proc.wait()
        with jobs_lock:
            job.exit_code = code
            job.duration = round(time.time() - start, 2)
            if code == 0 and Path(job.out_file).exists():
                job.status = "done"
            else:
                job.status = "error"
                job.error = f"Generation exited with code {code}."
    except Exception as exc:  # noqa: BLE001
        with jobs_lock:
            job.status = "error"
            job.duration = round(time.time() - start, 2)
            job.error = str(exc)
    finally:
        with jobs_lock:
            active_job_id = None


class Handler(SimpleHTTPRequestHandler):
    server_version = "SulphurMLXGUI/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write(f"[gui] {self.address_string()} - {fmt % args}\n")

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/":
            self.serve_file(STATIC / "index.html", "text/html; charset=utf-8")
            return
        if path == "/api/status":
            self.handle_status()
            return
        if path == "/api/history":
            self.handle_history()
            return
        if path.startswith("/api/jobs/"):
            self.handle_job(path.removeprefix("/api/jobs/"))
            return
        if path.startswith("/video/"):
            self.handle_video(path.removeprefix("/video/"))
            return
        if path.startswith("/static/"):
            self.serve_static(path.removeprefix("/static/"))
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_HEAD(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/":
            self.serve_file(STATIC / "index.html", "text/html; charset=utf-8", head_only=True)
            return
        if path.startswith("/static/"):
            self.serve_static(path.removeprefix("/static/"), head_only=True)
            return
        if path.startswith("/video/"):
            self.handle_video(path.removeprefix("/video/"), head_only=True)
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/generate":
            try:
                self.handle_generate(read_json(self))
            except ValueError as exc:
                json_response(self, {"error": str(exc)}, 400)
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def serve_static(self, rel: str, head_only: bool = False) -> None:
        safe = Path(unquote(rel))
        if safe.is_absolute() or ".." in safe.parts:
            self.send_error(HTTPStatus.BAD_REQUEST)
            return
        target = STATIC / safe
        types = {
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".html": "text/html; charset=utf-8",
        }
        self.serve_file(target, types.get(target.suffix, "application/octet-stream"), head_only=head_only)

    def serve_file(self, path: Path, content_type: str, head_only: bool = False) -> None:
        if not path.exists() or not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if not head_only:
            self.wfile.write(body)

    def handle_video(self, rel: str, head_only: bool = False) -> None:
        name = Path(unquote(rel)).name
        target = OUTPUT / name
        if not target.exists():
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        size = target.stat().st_size
        range_header = self.headers.get("Range")
        if range_header and range_header.startswith("bytes="):
            start_raw, _, end_raw = range_header.removeprefix("bytes=").partition("-")
            start = int(start_raw) if start_raw else 0
            end = int(end_raw) if end_raw else size - 1
            end = min(end, size - 1)
            if start >= size or end < start:
                self.send_error(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                return
            length = end - start + 1
            self.send_response(HTTPStatus.PARTIAL_CONTENT)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Length", str(length))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.end_headers()
            if head_only:
                return
            with target.open("rb") as fh:
                fh.seek(start)
                remaining = length
                while remaining > 0:
                    chunk = fh.read(min(1024 * 512, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    self.wfile.write(chunk)
            return

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "video/mp4")
        self.send_header("Content-Length", str(size))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        if head_only:
            return
        with target.open("rb") as fh:
            while chunk := fh.read(1024 * 512):
                self.wfile.write(chunk)

    def handle_generate(self, data: dict[str, Any]) -> None:
        global active_job_id
        with jobs_lock:
            if active_job_id is not None:
                json_response(self, {"error": "A generation is already running.", "job_id": active_job_id}, 409)
                return

        job_id = uuid.uuid4().hex
        command, out_path, prompt = build_command(data, job_id)
        job = Job(
            id=job_id,
            status="queued",
            created_at=time.time(),
            command=command,
            prompt=prompt,
            out_file=str(out_path),
            params=data,
        )
        with jobs_lock:
            jobs[job_id] = job
            active_job_id = job_id
        threading.Thread(target=run_job, args=(job_id,), daemon=True).start()
        json_response(self, {"job": job.public()}, 202)

    def handle_job(self, job_id: str) -> None:
        with jobs_lock:
            job = jobs.get(job_id)
            if job is None:
                json_response(self, {"error": "Job not found."}, 404)
                return
            json_response(self, {"job": job.public()})

    def handle_status(self) -> None:
        with jobs_lock:
            active = jobs.get(active_job_id).public() if active_job_id and active_job_id in jobs else None
        json_response(
            self,
            {
                "root": str(ROOT),
                "runtime_ready": (RUNTIME / "pyproject.toml").exists(),
                "active_job": active,
                "outputs": list_outputs(limit=8),
            },
        )

    def handle_history(self) -> None:
        json_response(self, {"outputs": list_outputs(limit=24)})


def list_outputs(limit: int = 12) -> list[dict[str, Any]]:
    if not OUTPUT.exists():
        return []
    items = sorted(OUTPUT.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    results: list[dict[str, Any]] = []
    for path in items[:limit]:
        meta_path = path.with_suffix(".json")
        meta: dict[str, Any] = {}
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                meta = {}
        results.append(
            {
                "filename": path.name,
                "video_url": f"/video/{path.name}",
                "size": path.stat().st_size,
                "created_at": path.stat().st_mtime,
                "prompt": meta.get("prompt", ""),
                "resolution": f"{meta.get('width', '?')}x{meta.get('height', '?')}",
                "frames": meta.get("frames", ""),
            }
        )
    return results


def main() -> None:
    port = int(os.environ.get("SULPHUR_GUI_PORT", "8786"))
    host = os.environ.get("SULPHUR_GUI_HOST", "127.0.0.1")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Sulphur 2 MLX GUI running at http://{host}:{port}")
    print(f"Project: {ROOT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping GUI server.")


if __name__ == "__main__":
    main()
