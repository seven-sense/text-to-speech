# PyInstaller spec for the Qwen3-TTS desktop converter.
#
# Build (run on the OS you want a binary for -- PyInstaller does NOT
# cross-compile):
#
#     python build.py
#   or
#     pyinstaller qwen_tts_tts.spec --noconfirm
#
# Produces a self-contained folder under dist/Qwen3-TTS-Converter/
# (and a .app bundle as well on macOS).
#
# Note: the Qwen3-TTS model weights (~1.2 GB) are NOT bundled. They are
# downloaded from Hugging Face into the user's cache on first conversion.

import sys

from PyInstaller.utils.hooks import collect_all

APP_NAME = "Qwen3-TTS-Converter"

# Packages whose code, data files and dynamic libraries must travel with
# the app. collect_all pulls everything PyInstaller would otherwise miss.
_BUNDLE_PACKAGES = [
    "qwen_tts",
    "transformers",
    "tokenizers",
    "safetensors",
    "huggingface_hub",
    "torch",
    "torchaudio",
    "soundfile",
    "soxr",
    "librosa",
    "audioread",
    "lazy_loader",
    "numpy",
    "scipy",
    "sklearn",
    "numba",
    "regex",
]

datas, binaries, hiddenimports = [], [], []
for package in _BUNDLE_PACKAGES:
    try:
        pkg_datas, pkg_binaries, pkg_hidden = collect_all(package)
        datas += pkg_datas
        binaries += pkg_binaries
        hiddenimports += pkg_hidden
    except Exception as exc:  # package not installed -- skip it
        print(f"[spec] skipping '{package}': {exc}")

# Heavy, unused frameworks -- excluding them greatly shrinks the build.
excludes = [
    "tensorflow", "tensorboard", "keras", "tf_keras", "jax",
    "torchvision", "gradio", "gradio_client", "fastapi", "uvicorn",
    "matplotlib", "IPython", "notebook", "pytest",
]

a = Analysis(
    ["run_app.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,          # windowed GUI app -- no terminal window
    disable_windowed_traceback=False,
    argv_emulation=True,    # lets users drag a file onto the app (macOS)
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=APP_NAME,
)

# On macOS, also produce a double-clickable .app bundle.
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name=f"{APP_NAME}.app",
        icon=None,
        bundle_identifier="com.qwentts.converter",
        info_plist={
            "NSHighResolutionCapable": True,
            "CFBundleDisplayName": "Qwen3-TTS Converter",
        },
    )
