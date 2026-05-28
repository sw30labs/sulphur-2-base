#!/usr/bin/env python3
"""Small, safe wrapper around dgrauet/ltx-2-mlx for Sulphur 2."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime" / "ltx-2-mlx"
OUTPUT = ROOT / "output"
LOCAL_MODEL = ROOT / "models" / "sulphur-2-distill-mlx-q4"

DEFAULT_MODEL = "MLXBits/sulphur-2-distill-mlx-q4"
DEFAULT_GEMMA = "mlx-community/gemma-3-12b-it-4bit"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return (slug[:48] or "sulphur").strip("_")


def default_model() -> str:
    if (LOCAL_MODEL / "config.json").exists():
        return str(LOCAL_MODEL)
    return DEFAULT_MODEL


def resolve_out(path: str | None, prompt: str) -> Path:
    if path:
        out = Path(path).expanduser()
        if not out.is_absolute():
            out = OUTPUT / out
    else:
        OUTPUT.mkdir(parents=True, exist_ok=True)
        stamp = int(time.time())
        out = OUTPUT / f"{stamp}_{slugify(prompt)}.mp4"
    if out.suffix.lower() != ".mp4":
        out = out.with_suffix(".mp4")
    out.parent.mkdir(parents=True, exist_ok=True)
    return out


def require_runtime() -> None:
    if not (RUNTIME / "pyproject.toml").exists():
        raise SystemExit("Runtime is missing. Run ./install.sh first.")
    if shutil.which("uv") is None:
        raise SystemExit("uv is missing. Run ./install.sh first.")


def frame_count(value: str) -> int:
    frames = int(value)
    if frames < 9:
        raise argparse.ArgumentTypeError("frames must be >= 9")
    if (frames - 1) % 8 != 0:
        raise argparse.ArgumentTypeError("frames must satisfy 8k + 1, for example 49, 65, 97")
    return frames


def dimension(value: str) -> int:
    size = int(value)
    if size < 128 or size > 1920:
        raise argparse.ArgumentTypeError("dimension must be between 128 and 1920")
    if size % 32 != 0:
        raise argparse.ArgumentTypeError("dimension must be divisible by 32")
    return size


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate Sulphur 2 video with the MLX LTX runtime.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--prompt", "-p", help="Text prompt. If omitted, stdin is used.")
    parser.add_argument("--image", "-i", help="Optional reference image path for image-to-video.")
    parser.add_argument("--out", "-o", help="Output MP4 path. Relative paths land in output/.")
    parser.add_argument("--model", "-m", default=None, help="HF repo ID or local model path.")
    parser.add_argument("--gemma", default=DEFAULT_GEMMA, help="Gemma text encoder model.")
    parser.add_argument("--height", "-H", type=dimension, default=320, help="Video height.")
    parser.add_argument("--width", "-W", type=dimension, default=512, help="Video width.")
    parser.add_argument("--frames", "-f", type=frame_count, default=65, help="Frame count, 8k + 1.")
    parser.add_argument("--frame-rate", type=float, default=24.0, help="Output frame rate.")
    parser.add_argument("--seed", "-s", type=int, default=-1, help="Seed; -1 means random.")
    parser.add_argument("--stage1-steps", type=int, default=8, help="Distilled stage 1 steps.")
    parser.add_argument("--stage2-steps", type=int, default=3, help="Distilled stage 2 steps.")
    parser.add_argument("--tile-frames", type=int, default=1, help="Temporal tile count.")
    parser.add_argument("--tile-spatial", type=int, default=1, help="Spatial tile count per axis.")
    parser.add_argument("--tile-overlap", type=int, default=2, help="Tile overlap.")
    parser.add_argument("--enhance-prompt", action="store_true", help="Use ltx-2-mlx Gemma prompt enhancement.")
    parser.add_argument("--no-low-ram", action="store_true", help="Disable low RAM block streaming.")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress ltx-2-mlx progress output.")
    parser.add_argument("--info", action="store_true", help="Show model info instead of generating.")
    return parser


def stream_command(command: list[str]) -> int:
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    proc = subprocess.Popen(
        command,
        cwd=str(RUNTIME),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        print(line, end="", flush=True)
    return proc.wait()


def write_sidecar(out_path: Path, args: argparse.Namespace, command: list[str], started: float) -> None:
    meta = {
        "prompt": args.prompt,
        "image": args.image,
        "model": args.model or default_model(),
        "height": args.height,
        "width": args.width,
        "frames": args.frames,
        "frame_rate": args.frame_rate,
        "seed": args.seed,
        "stage1_steps": args.stage1_steps,
        "stage2_steps": args.stage2_steps,
        "low_ram": not args.no_low_ram,
        "tile_frames": args.tile_frames,
        "tile_spatial": args.tile_spatial,
        "tile_overlap": args.tile_overlap,
        "enhance_prompt": args.enhance_prompt,
        "duration_wall": round(time.time() - started, 2),
        "output": str(out_path),
        "command": command,
    }
    out_path.with_suffix(".json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    require_runtime()

    model = args.model or default_model()
    if args.info:
        command = ["uv", "run", "ltx-2-mlx", "info", "--model", model]
        return stream_command(command)

    prompt = (args.prompt or "").strip()
    if not prompt:
        if sys.stdin.isatty():
            prompt = input("Prompt: ").strip()
        else:
            prompt = sys.stdin.read().strip()
    if not prompt:
        parser.error("--prompt is required")
    args.prompt = prompt

    if args.image:
        image = Path(args.image).expanduser()
        if not image.exists():
            parser.error(f"image not found: {image}")
        args.image = str(image)

    out_path = resolve_out(args.out, prompt)
    command = [
        "uv",
        "run",
        "ltx-2-mlx",
        "generate",
        "--distilled",
        "--prompt",
        prompt,
        "--output",
        str(out_path),
        "--model",
        model,
        "--gemma",
        args.gemma,
        "--height",
        str(args.height),
        "--width",
        str(args.width),
        "--frames",
        str(args.frames),
        "--frame-rate",
        f"{args.frame_rate:g}",
        "--seed",
        str(args.seed),
        "--stage1-steps",
        str(args.stage1_steps),
        "--stage2-steps",
        str(args.stage2_steps),
        "--tile-frames",
        str(args.tile_frames),
        "--tile-spatial",
        str(args.tile_spatial),
        "--tile-overlap",
        str(args.tile_overlap),
    ]
    if args.image:
        command.extend(["--image", args.image])
    if args.enhance_prompt:
        command.append("--enhance-prompt")
    if not args.no_low_ram:
        command.append("--low-ram")
    if args.quiet:
        command.append("--quiet")

    print("Sulphur MLX command:")
    print(" ".join(command))
    print()
    started = time.time()
    code = stream_command(command)
    if code == 0 and out_path.exists():
        write_sidecar(out_path, args, command, started)
        print(f"\nsaved: {out_path}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
