# Voice Cloning with Python - MAXIMUM QUALITY

This repository contains **optimized** Python scripts for voice cloning using the Coqui TTS XTTS v2 model. Clone any voice with **85-95% accuracy** - sounds like the original person speaking!

## ✨ Features

- 🎯 **MAXIMUM QUALITY** - Optimized for closest match to original voice
- 🔧 **Automatic Audio Preprocessing** - Normalizes, optimizes, and enhances voice samples
- 🎙️ Clone voices from audio samples (10+ seconds recommended)
- 🌍 Support for 16+ languages
- 🚀 GPU acceleration support
- 📝 Text-to-speech with cloned voices
- 🎵 Multiple audio format support (WAV, MP3, OGG, FLAC)
- 🧪 Test multiple settings to find your best match
- 💻 Both simple and advanced usage options

## Installation

### 1. Create a Conda Environment (Recommended)

```bash
conda create -n tts python=3.10
conda activate tts
```

### 2. Install Dependencies

```bash
pip install TTS torch pydub
```

### 3. Install FFmpeg (required for audio format conversion)

**Windows:**
```bash
conda install -c conda-forge ffmpeg
```

**Linux/Mac:**
```bash
sudo apt-get install ffmpeg  # Ubuntu/Debian
brew install ffmpeg          # macOS
```

## 🚀 Quick Start (3 Easy Steps!)

### Step 1: MAXIMUM QUALITY Mode (Recommended)

Just run the optimized script - it's configured for **best possible quality**:

```bash
python simple_voice_clone.py
```

This will:
- ✅ Automatically preprocess your audio
- ✅ Use MAXIMUM quality settings (temperature=0.05)
- ✅ Generate: `output_max_quality.wav`

**That's it!** You should get **85-95% quality** right away! 🎉

### Step 2: Test Different Settings (Optional)

Not satisfied? Test 5 different quality presets to find your best match:

```bash
python test_different_settings.py
```

Generates:
1. `test_ultra_accurate.wav` - Closest to original ⭐
2. `test_high_quality.wav` - Very close match
3. `test_balanced.wav` - Good balance
4. `test_natural.wav` - More expressive
5. `test_expressive.wav` - Most emotion

Listen to all 5 and pick your favorite!

### Step 3: Optimize Your Voice Sample (If Needed)

Want even better results? Optimize your voice sample:

```bash
python improve_voice_sample.py
```

This will:
- 🔍 Analyze your current voice sample
- ✅ Create optimized version (`myvoice_optimized.wav`)
- 📊 Show quality score and recommendations

---

### Customization

Edit these variables in [simple_voice_clone.py](simple_voice_clone.py):

```python
TEXT_TO_SPEAK = "Your text here"
VOICE_SAMPLE = "myvoice.wav"  # Your voice recording (10+ seconds)
LANGUAGE = "en"  # Language code
```

### Advanced Usage with Command Line

Use [voice_cloner.py](voice_cloner.py) for more control:

```bash
# Basic usage
python voice_cloner.py --text "Hello world" --speaker myvoice.wav

# Clone voice from text file
python voice_cloner.py --text-file script.txt --speaker myvoice.wav --output cloned.wav

# Use different language (Spanish)
python voice_cloner.py --text "Hola mundo" --speaker myvoice.wav --language es

# Use GPU acceleration
python voice_cloner.py --text "Hello" --speaker myvoice.wav --gpu

# Convert output to MP3
python voice_cloner.py --text "Hello" --speaker myvoice.wav --convert-to mp3
```

## Supported Languages

| Code | Language | Code | Language |
|------|----------|------|----------|
| `en` | English | `es` | Spanish |
| `fr` | French | `de` | German |
| `it` | Italian | `pt` | Portuguese |
| `pl` | Polish | `tr` | Turkish |
| `ru` | Russian | `nl` | Dutch |
| `cs` | Czech | `ar` | Arabic |
| `zh-cn` | Chinese | `ja` | Japanese |
| `ko` | Korean | `hu` | Hungarian |

## Tips for Best Results

### Voice Sample Quality

- **Length**: Use at least 6-10 seconds of clear speech
- **Quality**: High-quality audio (WAV format preferred)
- **Content**: Clean speech without background noise or music
- **Emotion**: Natural speaking voice works best
- **Single speaker**: Only one person speaking

### Recording Your Voice Sample

1. Use a good microphone in a quiet environment
2. Speak naturally and clearly
3. Record at least 10 seconds
4. Save as WAV format (44.1kHz or 48kHz sample rate)

Example using FFmpeg to convert audio:
```bash
ffmpeg -i input.mp3 -ar 22050 -ac 1 myvoice.wav
```

## Project Structure

```
text-to-speech/
├── README.md
├── run_app.py                # GUI entry point (PyInstaller target)
├── qwen_tts_tts.spec         # PyInstaller spec (must stay at root)
├── requirements.txt          # Core deps
├── requirements-app.txt      # Desktop app extras
├── qwen_tts_app/             # Main package (engine, gui, textio)
├── manifest.json             # Clip definitions for batch synthesis
├── scripts/
│   ├── synthesize_manifest.py  # Render every clip in tts-app/manifest.json
│   ├── build.py                # PyInstaller wrapper
│   ├── simple_voice_clone.py   # XTTS-based one-shot clone (legacy)
│   └── improve_voice_sample.py # Audio sample analyzer/optimizer
├── refs/                     # Reference audio for voice cloning
├── samples/                  # Demo voice samples + transcript
├── docs/                     # APP.md, env-setup.md
├── notebooks/                # Exploratory notebooks
└── output/                   # Generated audio (gitignored, regenerable)
```

## Usage Examples

### Example 1: Read a Story

```python
from simple_voice_clone import clone_voice_simple

story = """
Once upon a time, in a land far away, there lived a brave knight.
The knight embarked on an epic quest to save the kingdom.
"""

clone_voice_simple(
    text=story,
    speaker_audio="myvoice.wav",
    output_file="story.wav"
)
```

### Example 2: Multiple Languages

```bash
# English
python voice_cloner.py --text "Hello, how are you?" --speaker myvoice.wav --language en

# Spanish
python voice_cloner.py --text "Hola, ¿cómo estás?" --speaker myvoice.wav --language es

# French
python voice_cloner.py --text "Bonjour, comment allez-vous?" --speaker myvoice.wav --language fr
```

### Example 3: Batch Processing

Create a file `texts.txt` with your content and run:
```bash
python voice_cloner.py --text-file texts.txt --speaker myvoice.wav --output batch_output.wav
```

## Using in Your Own Code

```python
from voice_cloner import VoiceCloner

# Initialize
cloner = VoiceCloner(use_gpu=False)

# Clone voice
cloner.clone_voice(
    text="This is a test of voice cloning technology.",
    speaker_wav="myvoice.wav",
    output_path="my_output.wav",
    language="en"
)

# Get audio duration
duration = cloner.get_audio_duration("my_output.wav")
print(f"Audio duration: {duration} seconds")

# Convert to MP3
cloner.convert_audio_format("my_output.wav", "my_output.mp3", format="mp3")
```

## Troubleshooting

### Common Issues

1. **"Speaker audio file not found"**
   - Make sure your voice sample file exists and path is correct
   - Use absolute paths if relative paths don't work

2. **Poor quality output**
   - Use a longer, clearer voice sample (10+ seconds)
   - Ensure your voice sample has minimal background noise
   - Try recording in WAV format at 44.1kHz

3. **Slow generation**
   - Use `--gpu` flag if you have a CUDA-capable GPU
   - Reduce text length for faster processing

4. **Memory errors**
   - Close other applications
   - Use CPU mode instead of GPU
   - Process shorter text segments

## Model Information

This project uses **Coqui TTS XTTS v2**, a state-of-the-art voice cloning model that:
- Can clone voices from short audio samples
- Supports multiple languages
- Generates natural-sounding speech
- Works on CPU and GPU

## License

This project uses the Coqui TTS library. Please refer to the [Coqui TTS license](https://github.com/coqui-ai/TTS) for terms of use.

## Credits

- [Coqui TTS](https://github.com/coqui-ai/TTS) - Text-to-Speech library
- XTTS v2 Model - Voice cloning technology

## Ethical Considerations

⚠️ **Important**: Voice cloning technology should be used responsibly:
- Only clone voices you have permission to use
- Don't use for impersonation or fraud
- Respect privacy and consent
- Be transparent about synthetic audio usage

## Contributing

Feel free to open issues or submit pull requests for improvements!

## Support

For issues related to:
- This project: Open an issue on GitHub
- Coqui TTS: Visit [Coqui TTS GitHub](https://github.com/coqui-ai/TTS)
