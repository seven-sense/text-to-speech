"""Launch the Qwen3-TTS desktop converter.

This is the entry point used both for running from source::

    python run_app.py [optional_input_file]

and as the script bundled by PyInstaller (see ``qwen_tts_tts.spec``).
"""

from qwen_tts_app.gui import main

if __name__ == "__main__":
    main()
