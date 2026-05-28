# Sulphur 2 Base Local

Local Apple Silicon project for **SulphurAI/Sulphur-2-base**, modeled after the
Stable Audio 3 desktop project. It wraps the native MLX LTX runtime with a small
CLI, installer, and browser UI.

This project does not vendor the huge model files. By default it points to:

- Video model: `MLXBits/sulphur-2-distill-mlx-q4`
- Optional prompt enhancer: `MLXBits/sulphur-promptenhancer-mlx-q8`
- Runtime: `dgrauet/ltx-2-mlx`

## Quick Start

```bash
./install.sh -y
./gui.sh
```

Open the printed local URL, usually:

```text
http://127.0.0.1:8786
```

Generate from the terminal:

```bash
./sulphur --prompt "A handheld cinematic shot of a neon street market at night, rain glistens on umbrellas, low synth hum, distant traffic, slow dolly forward" --frames 65 --height 320 --width 512
```

## Download Weights Up Front

The first real generation will download model files if they are not already in
your Hugging Face cache. That includes the Sulphur video bundle plus the Gemma
text encoder used by `ltx-2-mlx`. To download the Sulphur MLX Q4 bundle into
this project instead:

```bash
./install.sh -y --download-model
```

The Q4 video bundle is roughly 34 GB. The prompt enhancer is separate and about
10 GB:

```bash
./install.sh -y --download-prompt-enhancer
```

The GUI's `Enhance` checkbox uses the `ltx-2-mlx` Gemma prompt enhancer. The
Sulphur prompt-enhancer download is provided for manual/LM Studio-style
workflows.

## CLI Defaults

The `./sulphur` wrapper runs:

```bash
ltx-2-mlx generate --distilled --model MLXBits/sulphur-2-distill-mlx-q4
```

Defaults are intentionally conservative for Apple Silicon:

| Option | Default |
|---|---:|
| Width | 512 |
| Height | 320 |
| Frames | 65 |
| Frame rate | 24 |
| Stage 1 steps | 8 |
| Stage 2 steps | 3 |
| Low RAM streaming | on |

Frame counts should follow `8k + 1`. Useful values: `49`, `65`, `81`, `97`,
`121`, `145`, `161`, `193`.

## Files

```text
sulphur-2-base/
├── install.sh                 # clones/syncs dgrauet/ltx-2-mlx
├── sulphur                    # terminal wrapper
├── gui.sh                     # starts the local web UI
├── scripts/sulphur_mlx.py     # safe command builder around ltx-2-mlx
├── gui/                       # stdlib web server + static UI
├── models/                    # optional local HF downloads
├── output/gui/                # generated MP4s + JSON sidecars
└── runtime/ltx-2-mlx/         # runtime checkout created by install.sh
```

## Notes

- Apple Silicon is required. MLX is Metal-backed.
- `ffmpeg` is required by the runtime for MP4 output.
- The original SulphurAI repo is Diffusers/GGUF. The MLX path uses the
  third-party MLXBits conversion of Sulphur 2, which is based on the same model.
