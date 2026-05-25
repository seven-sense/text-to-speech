# Qwen3 Text-to-Speech Toolkit

This repository contains a desktop text-to-speech app built on `qwen-tts` plus
supporting scripts for batch clip generation and legacy Coqui XTTS voice
cloning experiments.

## What Is In This Repo

- `qwen_tts_app/`: Tkinter desktop app that converts `.txt`/`.md` files to
  spoken `.wav` audio.
- `scripts/synthesize_manifest.py`: batch synthesis from `manifest.json` into
  per-clip and combined outputs.
- `scripts/build.py`: PyInstaller wrapper for building a desktop binary.
- `scripts/simple_voice_clone.py` and `scripts/improve_voice_sample.py`:
  older Coqui XTTS-based voice cloning utilities.

## Quick Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements-app.txt
```

Optional (only if you want the legacy Coqui XTTS scripts):

```bash
pip install -r requirements.txt
```

Notes:

- First Qwen3 synthesis run downloads model weights from Hugging Face
  (roughly 1.2 GB).
- CUDA is used automatically when available; otherwise CPU is used.
- For `pydub` workflows and broad audio format support, install FFmpeg.

## Run The Desktop App

From repo root:

```bash
python run_app.py
```

Equivalent:

```bash
python -m qwen_tts_app
```

Optional preload of an input file:

```bash
python run_app.py path/to/input.md
```

### App Behavior

- Input: `.txt`, `.md`, `.markdown`, `.text`
- Markdown is stripped to plain speakable text.
- Long text is chunked (~350 chars/chunk) and synthesized progressively.
- Output: `.wav`
- Voice modes:
  - Preset voice: `Aiden` or `Serena`
  - Clone voice: requires both reference audio and a matching transcript file
- Language dropdown currently includes:
  - English, Chinese, German, Italian, Portuguese, Spanish, Japanese, Korean,
    French, Russian

## Build Standalone App (PyInstaller)

Run on the target operating system (PyInstaller does not cross-compile):

```bash
python scripts/build.py
```

This uses [`qwen_tts_tts.spec`](qwen_tts_tts.spec) and writes output under
`dist/` (with `.app` bundle on macOS).

## Batch Synthesis From Manifest

Generate all clips listed in [`manifest.json`](manifest.json):

```bash
python scripts/synthesize_manifest.py
```

Outputs are written to:

- `output/clips/**/*.flac`
- `output/clips/**/*.mp3`
- `output/combined/full.flac`
- `output/combined/full.mp3`
- `output/combined/timestamps.json`

The script currently uses `refs/indian_female_calm.wav` plus a fixed reference
transcript for clone synthesis.

## Legacy Coqui XTTS Scripts

Run one-shot cloning experiment:

```bash
python scripts/simple_voice_clone.py
```

Analyze and optimize a reference sample:

```bash
python scripts/improve_voice_sample.py
```

These scripts are separate from the Qwen3 desktop app and rely on Coqui XTTS
(`TTS` package) plus `pydub`.

## Repository Layout

```text
.
├── README.md
├── run_app.py
├── qwen_tts_tts.spec
├── manifest.json
├── requirements-app.txt
├── requirements.txt
├── qwen_tts_app/
│   ├── __init__.py
│   ├── __main__.py
│   ├── engine.py
│   ├── gui.py
│   └── textio.py
├── scripts/
│   ├── build.py
│   ├── synthesize_manifest.py
│   ├── simple_voice_clone.py
│   └── improve_voice_sample.py
├── refs/
├── samples/
├── docs/
├── notebooks/
└── output/
```

## Responsible Use

Use cloned or synthetic voices only with proper consent and legal permission.
