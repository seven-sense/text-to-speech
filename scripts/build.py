"""Build a standalone desktop binary of the Qwen3-TTS converter.

Run this on the operating system you want a binary for -- PyInstaller does
not cross-compile, so build on Windows for the .exe, on macOS for the .app,
and on Linux for the Linux binary::

    python build.py

The result is written to ``dist/Qwen3-TTS-Converter/`` (plus a ``.app``
bundle on macOS). The Qwen3-TTS model weights are not bundled; they are
downloaded on first use.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from pathlib import Path

SPEC_FILE = "qwen_tts_tts.spec"
ROOT = Path(__file__).resolve().parent.parent


def ensure_pyinstaller() -> None:
    """Install PyInstaller into the current environment if it is missing."""
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("PyInstaller not found -- installing it...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "pyinstaller>=6.0"]
        )


def clean() -> None:
    """Remove output from a previous build."""
    for name in ("build", "dist"):
        target = ROOT / name
        if target.exists():
            print(f"Removing old {name}/ ...")
            shutil.rmtree(target, ignore_errors=True)


def main() -> int:
    print(f"Building Qwen3-TTS Converter for {platform.system()} "
          f"({platform.machine()})\n")

    ensure_pyinstaller()
    clean()

    cmd = [sys.executable, "-m", "PyInstaller", SPEC_FILE, "--noconfirm",
           "--clean"]
    print("Running:", " ".join(cmd), "\n")
    result = subprocess.call(cmd, cwd=ROOT)

    if result != 0:
        print("\nBuild FAILED.", file=sys.stderr)
        return result

    dist = ROOT / "dist"
    print("\nBuild complete. Output in:", dist)
    for item in sorted(dist.iterdir()):
        print("  -", item.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
