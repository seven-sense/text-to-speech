"""Synthesize every clip in manifest.json with qwen_tts.

Each clip is voiced with a delivery instruction matched to its tags, so
pranayama lines sound like a yoga instructor, physio lines sound like a
physiotherapist coaching a patient, ticks sound rhythmic, etc.

Outputs:
    output/clips/<id>.mp3
    output/clips/<id>.flac
    output/combined/full.mp3
    output/combined/full.flac
    output/combined/timestamps.json
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Sequence

import numpy as np
import soundfile as sf
import soxr
import torch

from qwen_tts import Qwen3TTSModel
from qwen_tts_app.engine import CLONE_MODEL_ID, select_device

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "manifest.json"
OUTPUT_DIR = ROOT / "output"
CLIPS_DIR = OUTPUT_DIR / "clips"
COMBINED_DIR = OUTPUT_DIR / "combined"

# Silence inserted between clips in the combined track.
GAP_SECONDS = 0.4

# Indian-English female reference for voice cloning.
# Source: skit-ai/emotion-tts (Calm-8.wav), CC BY-NC 4.0.
REF_AUDIO = ROOT / "refs" / "indian_female_calm.wav"
REF_TEXT = (
    "I agree completely about sleep being a key element in maintaining a "
    "healthy body. Lately, I've been only getting five or so hours, and I "
    "can feel how drained and vulnerable my body has become. How much do "
    "you sleep on average?"
)
LANGUAGE = "English"

# Delivery style, picked by the first tag that matches this priority list.
# Counts (no tags) and anything unmatched fall through to DEFAULT_INSTRUCT.
INSTRUCT_BY_TAG: dict[str, str] = {
    "pranayama": (
        "Speak as a calm, experienced yoga instructor guiding a student through "
        "a pranayama breathing practice. Tone is soothing, warm, and grounded. "
        "Pace is unhurried with gentle pauses between sentences, leaving room "
        "for the listener to breathe."
    ),
    "bhastrika": (
        "Speak as a yoga instructor preparing a student for forceful bhastrika "
        "breathwork. Tone is calm but focused and steady, with a sense of "
        "readiness building toward action."
    ),
    "physio": (
        "Speak as a clear, encouraging physiotherapist coaching a patient "
        "through a rehabilitation exercise. Tone is warm, instructional, and "
        "firm on safety cues. Emphasize key action words like lock, bend, "
        "raise, hold, and lower."
    ),
    "tick": (
        "Speak the single word briefly and rhythmically, as a one-syllable "
        "breath cue paced to match an inhale or exhale. Crisp, short, even."
    ),
    "ui": (
        "Speak in a warm, friendly, concise notification tone, like a "
        "supportive app voice confirming progress."
    ),
}

DEFAULT_INSTRUCT = (
    "Count clearly and steadily, like a trainer marking repetitions during "
    "an exercise. Even pace, neutral tone, no rush."
)

TAG_PRIORITY = ["physio", "pranayama", "bhastrika", "tick", "ui"]


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def instruct_for(clip: dict) -> str:
    tags: Sequence[str] = clip.get("tags") or []
    for tag in TAG_PRIORITY:
        if tag in tags:
            return INSTRUCT_BY_TAG[tag]
    return DEFAULT_INSTRUCT


def to_mono(audio: np.ndarray) -> np.ndarray:
    if audio.ndim == 1:
        return audio
    return audio.mean(axis=1).astype(np.float32)


def resample(audio: np.ndarray, src_sr: int, dst_sr: int) -> np.ndarray:
    if src_sr == dst_sr:
        return audio
    return soxr.resample(audio, src_sr, dst_sr).astype(np.float32)


def silence(seconds: float, sample_rate: int) -> np.ndarray:
    return np.zeros(int(round(seconds * sample_rate)), dtype=np.float32)


def write_flac(path: Path, audio: np.ndarray, sample_rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), audio, sample_rate, format="FLAC", subtype="PCM_16")


def write_mp3(path: Path, audio: np.ndarray, sample_rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), audio, sample_rate, format="MP3")


def load_model():
    device = select_device()
    log(f"Device: {device.upper()}")
    log(f"Loading {CLONE_MODEL_ID}...")
    model = Qwen3TTSModel.from_pretrained(
        CLONE_MODEL_ID,
        device_map=device,
        torch_dtype=torch.float32,
        trust_remote_code=True,
    )
    log("Model ready.")
    return model


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text())
    target_sr = int(manifest.get("sampleRate", 48000))
    clips = manifest["clips"]
    log(f"Loaded manifest with {len(clips)} clips (target sample rate {target_sr}).")

    model = load_model()

    combined: list[np.ndarray] = []
    timestamps: list[dict] = []
    cursor = 0.0

    for index, clip in enumerate(clips, start=1):
        clip_id = clip["id"]
        text = clip.get("text", "") or ""
        expected_ms = clip.get("expectedDurationMs")
        style = instruct_for(clip)
        style_label = next(
            (tag for tag in TAG_PRIORITY if tag in (clip.get("tags") or [])),
            "count",
        )
        log(f"({index}/{len(clips)}) [{style_label}] {clip_id}: {text[:60]!r}")

        if not text.strip():
            duration = (expected_ms or 350) / 1000.0
            audio = silence(duration, target_sr)
        else:
            wavs, sr = model.generate_voice_clone(
                text=text,
                language=LANGUAGE,
                ref_audio=str(REF_AUDIO),
                ref_text=REF_TEXT,
                instruct=style,
                flash_attn=False,
            )
            audio = to_mono(np.asarray(wavs[0], dtype=np.float32).reshape(-1))
            audio = resample(audio, sr, target_sr)
            audio = np.clip(audio, -1.0, 1.0).astype(np.float32)

        write_flac(CLIPS_DIR / f"{clip_id}.flac", audio, target_sr)
        write_mp3(CLIPS_DIR / f"{clip_id}.mp3", audio, target_sr)

        duration = len(audio) / target_sr
        start = cursor
        end = start + duration
        timestamps.append(
            {
                "id": clip_id,
                "text": text,
                "style": style_label,
                "start": round(start, 3),
                "end": round(end, 3),
                "duration": round(duration, 3),
            }
        )

        combined.append(audio)
        cursor = end

        if index != len(clips):
            gap = silence(GAP_SECONDS, target_sr)
            combined.append(gap)
            cursor += GAP_SECONDS

    full = np.concatenate(combined) if combined else np.zeros(0, dtype=np.float32)
    write_flac(COMBINED_DIR / "full.flac", full, target_sr)
    write_mp3(COMBINED_DIR / "full.mp3", full, target_sr)

    (COMBINED_DIR / "timestamps.json").write_text(
        json.dumps(
            {
                "sampleRate": target_sr,
                "channels": 1,
                "gapSeconds": GAP_SECONDS,
                "totalDuration": round(len(full) / target_sr, 3),
                "entries": timestamps,
            },
            indent=2,
        )
    )

    log(f"Done. Combined duration: {len(full)/target_sr:.2f}s.")
    log(f"Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
