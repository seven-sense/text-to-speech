"""
Maximum Quality Voice Cloning Script
Optimized for most accurate voice cloning - as if the original person is speaking
"""

import os
import torch
from TTS.api import TTS
from TTS.tts.configs import xtts_config
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range
import warnings

warnings.filterwarnings('ignore')


def preprocess_audio_for_best_quality(speaker_audio):
    """
    Preprocess audio for maximum cloning accuracy
    Returns path to optimized temporary file
    """
    print("🔧 Preprocessing audio for maximum quality...")

    # Load audio
    audio = AudioSegment.from_file(speaker_audio)

    # Convert to mono if stereo
    if audio.channels > 1:
        audio = audio.set_channels(1)
        print("   ✓ Converted to mono")

    # Set optimal sample rate for XTTS
    audio = audio.set_frame_rate(22050)
    print("   ✓ Optimized sample rate")

    # Normalize volume for consistency
    audio = normalize(audio)
    print("   ✓ Normalized volume")

    # Apply gentle compression for consistent voice level
    audio = compress_dynamic_range(
        audio,
        threshold=-20.0,
        ratio=3.0,
        attack=5.0,
        release=50.0
    )
    print("   ✓ Applied dynamic compression")

    # Remove silence from edges but keep natural pauses
    audio = audio.strip_silence(silence_thresh=-40, padding=150)
    print("   ✓ Trimmed edges")

    # Optimal length: 10-30 seconds for best results
    duration = len(audio) / 1000.0
    if duration > 30:
        # Take middle section for best quality
        start_ms = (len(audio) - 30000) // 2
        audio = audio[start_ms:start_ms + 30000]
        print(f"   ✓ Using middle 30s section (original: {duration:.1f}s)")
    elif duration < 6:
        print(f"   ⚠️  Warning: Audio is short ({duration:.1f}s). 10+ seconds recommended")

    # Save preprocessed audio
    temp_file = "temp_preprocessed_voice.wav"
    audio.export(temp_file, format="wav")
    print(f"   ✓ Preprocessed audio ready ({len(audio)/1000.0:.1f}s)\n")

    return temp_file


def clone_voice_simple(text, speaker_audio, output_file="cloned_voice.wav", language="en", preprocess=True):
    """
    Maximum quality voice cloning - makes it sound like the original person

    Args:
        text (str): The text you want to speak
        speaker_audio (str): Path to your voice sample (WAV file, at least 6 seconds)
        output_file (str): Where to save the output
        language (str): Language code (en, es, fr, de, it, pt, etc.)
        preprocess (bool): Automatically optimize audio for best results (recommended: True)

    Returns:
        str: Path to the generated audio file
    """
    print("🎙️  Maximum Quality Voice Cloning Started...")
    print(f"📝 Text: {text[:100]}..." if len(text) > 100 else f"📝 Text: {text}")
    print(f"🔊 Voice sample: {speaker_audio}")

    # Check if speaker audio exists
    if not os.path.exists(speaker_audio):
        raise FileNotFoundError(f"❌ Voice sample not found: {speaker_audio}")

    # Preprocess audio for best quality
    processed_audio = speaker_audio
    if preprocess:
        try:
            processed_audio = preprocess_audio_for_best_quality(speaker_audio)
        except Exception as e:
            print(f"   ⚠️  Preprocessing failed: {e}")
            print("   ℹ️  Using original audio\n")
            processed_audio = speaker_audio

    # Allow XTTS config for unpickling
    torch.serialization.add_safe_globals([xtts_config.XttsConfig])

    # Initialize TTS model
    print("⏳ Loading AI model (this may take a moment)...")
    use_gpu = torch.cuda.is_available()
    if use_gpu:
        print("   🚀 GPU detected - using hardware acceleration")

    tts = TTS(
        model_name="tts_models/multilingual/multi-dataset/xtts_v2",
        gpu=use_gpu
    )

    # Generate speech with MAXIMUM quality settings
    print("\n🎨 Generating speech with cloned voice...")
    print("   Settings: MAXIMUM QUALITY MODE")
    print("   • Ultra-low temperature for exact voice matching")
    print("   • High repetition penalty for natural speech")
    print("   • Optimized length ratio for best prosody\n")

    tts.tts_to_file(
        text=text,
        speaker_wav=processed_audio,
        language=language,
        file_path=output_file,
        # MAXIMUM QUALITY SETTINGS - Tuned for closest match to original voice
        temperature=0.05,  # ULTRA LOW = maximum similarity to reference voice
        repetition_penalty=10.0,  # MAXIMUM = most natural, no robotic repetitions
        speed=0.98,  # Slightly slower for clearer articulation
        length_penalty=1.0,  # Natural sentence length
        enable_text_splitting=True  # Better handling of long texts
    )

    # Clean up temporary preprocessed file
    if preprocess and processed_audio != speaker_audio:
        try:
            os.remove(processed_audio)
        except:
            pass

    # Get output info
    try:
        output_audio = AudioSegment.from_file(output_file)
        duration = len(output_audio) / 1000.0
        print(f"✅ Success! Audio saved to: {output_file}")
        print(f"   📊 Duration: {duration:.2f} seconds")
    except:
        print(f"\n✅ Success! Audio saved to: {output_file}")

    return output_file


# Example usage
if __name__ == "__main__":
    # ========== CONFIGURATION - EDIT THESE ==========
    TEXT_TO_SPEAK = """
    Hi, I'm Nithin—a professional overthinker, occasional snack enthusiast, and full-time champion of pressing "snooze" one too many times.
    I have a talent for turning ordinary situations into slightly chaotic adventures, like trying to make toast without setting off the smoke alarm or convincing myself that one more episode of a show won't turn into an all-night binge.
    Basically, I'm living proof that life is funnier when you don't take it too seriously… and when you have snacks within arm's reach.
    """

    from pathlib import Path
    VOICE_SAMPLE = str(Path(__file__).resolve().parent.parent / "samples" / "myvoice.wav")
    LANGUAGE = "en"  # Language: en, es, fr, de, it, pt, pl, tr, ru, nl, cs, ar, zh-cn, ja, ko, hu
    # ===============================================

    print("=" * 80)
    print("🎭 MAXIMUM QUALITY VOICE CLONING")
    print("=" * 80)
    print("\nThis will create the BEST possible clone of your voice.")
    print("Settings are optimized for maximum similarity to original speaker.\n")

    try:
        # Generate with maximum quality
        output = clone_voice_simple(
            text=TEXT_TO_SPEAK,
            speaker_audio=VOICE_SAMPLE,
            output_file="output_max_quality.wav",
            language=LANGUAGE,
            preprocess=True  # Auto-optimize audio (RECOMMENDED)
        )

        print("\n" + "=" * 80)
        print("🎉 VOICE CLONING COMPLETED!")
        print("=" * 80)
        print(f"\n📁 Output file: {output}")
        print("\n💡 TIPS FOR EVEN BETTER RESULTS:")
        print("   1. Use a 15-20 second voice sample (longer = better)")
        print("   2. Record in a quiet room with good microphone")
        print("   3. Speak naturally, not like reading")
        print("   4. Avoid background noise, music, or multiple speakers")
        print("\n   If quality is still not perfect, try recording a new")
        print("   voice sample following the tips above!")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 Common fixes:")
        print("   • Make sure 'myvoice.wav' exists in this folder")
        print("   • Check if pydub is installed: pip install pydub")
        print("   • Install ffmpeg: conda install -c conda-forge ffmpeg")
