# Qwen3-TTS Desktop Converter

A cross-platform desktop app that turns a **`.txt` or `.md` file** into spoken
audio (`.wav`) using **Qwen3-TTS**. It runs on Windows, macOS, and Linux.

You can speak the text with a **preset voice** or a **cloned voice** (cloned
from a reference recording). There is no emotion detection — every line is
spoken in a single calm, professional tone.

## Project layout

```
qwen_tts_app/
├── textio.py   # read .txt/.md, strip Markdown, split into chunks
├── engine.py   # Qwen3-TTS wrapper (preset + clone modes)
├── gui.py      # cross-platform Tkinter desktop GUI
└── __main__.py # `python -m qwen_tts_app`
run_app.py          # app entry point (used by source runs and PyInstaller)
build.py            # builds the standalone binary for the current OS
qwen_tts_tts.spec   # PyInstaller build recipe
```

## Run from source

```bash
# from the repo root, with the project venv active
python run_app.py
# optional: pre-load a file
python run_app.py path/to/story.md
```

A window opens. Choose your input file, pick a voice, choose where to save
the `.wav`, and click **Convert**. The first conversion downloads the
Qwen3-TTS model (~1.2 GB) from Hugging Face; later runs reuse the cache.

### Voice modes

- **Preset voice** — pick a built-in speaker (`Aiden`, `Serena`).
- **Clone a voice** — supply a **reference audio** file *and* a **transcript**
  text file whose contents exactly match what is spoken in that audio.

## Build a standalone binary (the "exe")

PyInstaller **does not cross-compile** — a build produces a binary only for
the OS it ran on. A Mac cannot build a Windows `.exe` or a Linux binary.

### Option A — build all three OSes with GitHub Actions (recommended)

[.github/workflows/build.yml](.github/workflows/build.yml) builds macOS,
Windows, and Linux in parallel on GitHub's runners — no extra machines
needed:

1. Commit and push this repo to GitHub.
2. **Actions** tab -> **Build desktop binaries** -> **Run workflow**.
3. When it finishes, download the three artifacts from the run page:
   `Qwen3-TTS-Converter-macOS / -Windows / -Linux`.

Pushing a tag (`git tag v1.0.0 && git push origin v1.0.0`) also publishes a
GitHub Release with all three binaries attached.

### Option B — build locally for the current OS only

Run the build on the OS you want a binary for:

| OS      | Run            | Output                                            |
|---------|----------------|---------------------------------------------------|
| Windows | `python build.py` | `dist\Qwen3-TTS-Converter\Qwen3-TTS-Converter.exe` |
| macOS   | `python build.py` | `dist/Qwen3-TTS-Converter.app` (+ folder build)    |
| Linux   | `python build.py` | `dist/Qwen3-TTS-Converter/Qwen3-TTS-Converter`     |

`build.py` installs PyInstaller if needed, cleans old output, then runs
`qwen_tts_tts.spec`. The result is a **one-folder** app: ship the whole
`Qwen3-TTS-Converter` folder (or the `.app`), not just the inner file.

The model weights are **not** bundled — the app downloads them on first use,
so the end user needs an internet connection the first time and roughly
1.5 GB of free disk for the Hugging Face cache.

## Notes

- **Device:** uses CUDA when available, otherwise CPU. Apple's MPS backend is
  skipped on purpose — Qwen3-TTS crashes on it. CPU synthesis is slower.
- **Markdown:** headings, lists, links, emphasis, code fences, and tables are
  reduced to plain prose before synthesis.
- **Long files:** text is split into ~350-character chunks; the chunks are
  synthesized one by one and joined with short silences.
