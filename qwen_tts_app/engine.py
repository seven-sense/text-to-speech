"""Qwen3-TTS synthesis engine.

Wraps the ``qwen_tts`` package with two modes:

* ``preset`` -- a built-in voice (Aiden / Serena) via the CustomVoice model.
* ``clone``  -- a voice cloned from a reference recording via the Base model.

Emotion detection is intentionally not used; every line is spoken with a
single calm, professional tone.
"""

from __future__ import annotations

from typing import Callable, Optional, Sequence

import numpy as np
import soundfile as sf

# Model checkpoints on the Hugging Face Hub (downloaded and cached on first use).
PRESET_MODEL_ID = "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice"
CLONE_MODEL_ID = "Qwen/Qwen3-TTS-12Hz-0.6B-Base"

# Built-in speakers for preset mode.
PRESET_SPEAKERS = ["Aiden", "Serena"]

# Fixed delivery style -- no emotion detection.
DEFAULT_INSTRUCT = "Speak with a calm, clear, and professional tone."

# Silence inserted between synthesized chunks, in seconds.
CHUNK_GAP_SECONDS = 0.3

LogFn = Callable[[str], None]
ProgressFn = Callable[[int, int, str], None]


def select_device() -> str:
    """Return the best available torch device string.

    Apple's MPS backend is deliberately skipped: Qwen3-TTS uses a
    ``multinomial`` sampling op that crashes on MPS, so CPU is used on Mac.
    """
    import torch

    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


class TTSEngine:
    """Loads Qwen3-TTS lazily and synthesizes audio from text chunks."""

    def __init__(self, log: Optional[LogFn] = None):
        self._log: LogFn = log or (lambda _msg: None)
        self._model = None
        self._loaded_mode: Optional[str] = None

    # -- model loading ----------------------------------------------------
    def _load(self, mode: str):
        """Load (and cache) the model checkpoint required by ``mode``."""
        if self._model is not None and self._loaded_mode == mode:
            return self._model

        import torch
        from qwen_tts import Qwen3TTSModel

        device = select_device()
        model_id = PRESET_MODEL_ID if mode == "preset" else CLONE_MODEL_ID

        self._log(f"Device: {device.upper()}")
        self._log(
            f"Loading model '{model_id}'.\n"
            "First run downloads ~1.2 GB from Hugging Face -- please wait..."
        )
        self._model = Qwen3TTSModel.from_pretrained(
            model_id,
            device_map=device,
            torch_dtype=torch.float32,
            trust_remote_code=True,
        )
        self._loaded_mode = mode
        self._log("Model ready.")
        return self._model

    # -- synthesis --------------------------------------------------------
    def convert(
        self,
        chunks: Sequence[str],
        *,
        mode: str,
        language: str = "English",
        speaker: Optional[str] = None,
        ref_audio: Optional[str] = None,
        ref_text: Optional[str] = None,
        progress: Optional[ProgressFn] = None,
    ) -> tuple[np.ndarray, int]:
        """Synthesize all ``chunks`` and return ``(audio, sample_rate)``.

        ``mode`` is ``"preset"`` (requires ``speaker``) or ``"clone"``
        (requires ``ref_audio`` and ``ref_text``).
        """
        if not chunks:
            raise ValueError("There is no text to synthesize.")

        if mode == "preset":
            if not speaker:
                raise ValueError("A preset speaker must be selected.")
            model = self._load("preset")

            def generate(text: str):
                return model.generate_custom_voice(
                    text=text,
                    speaker=speaker,
                    language=language,
                    instruct=DEFAULT_INSTRUCT,
                    flash_attn=False,
                )

        elif mode == "clone":
            if not ref_audio or not ref_text:
                raise ValueError(
                    "Voice cloning needs both a reference audio file and "
                    "its transcript."
                )
            model = self._load("clone")

            def generate(text: str):
                return model.generate_voice_clone(
                    text=text,
                    language=language,
                    ref_audio=ref_audio,
                    ref_text=ref_text,
                    instruct=DEFAULT_INSTRUCT,
                    flash_attn=False,
                )

        else:
            raise ValueError(f"Unknown mode '{mode}'.")

        audio_parts: list[np.ndarray] = []
        sample_rate: Optional[int] = None
        total = len(chunks)

        for index, chunk in enumerate(chunks, start=1):
            if progress:
                progress(index, total, chunk)
            wavs, sample_rate = generate(chunk)
            audio_parts.append(np.asarray(wavs[0], dtype=np.float32).reshape(-1))

        if sample_rate is None:
            raise RuntimeError("Synthesis produced no audio.")

        merged = _join_with_silence(audio_parts, sample_rate)
        return np.clip(merged, -1.0, 1.0), sample_rate


def _join_with_silence(parts: list[np.ndarray], sample_rate: int) -> np.ndarray:
    """Concatenate audio segments with a short silence gap between them."""
    if len(parts) == 1:
        return parts[0]
    gap = np.zeros(int(sample_rate * CHUNK_GAP_SECONDS), dtype=np.float32)
    pieces: list[np.ndarray] = []
    for index, part in enumerate(parts):
        if index:
            pieces.append(gap)
        pieces.append(part)
    return np.concatenate(pieces)


def save_wav(path: str, audio: np.ndarray, sample_rate: int) -> None:
    """Write ``audio`` to ``path`` as a WAV file."""
    sf.write(path, audio, sample_rate)
