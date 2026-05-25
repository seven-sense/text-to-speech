"""Cross-platform Tkinter desktop GUI for the Qwen3-TTS converter.

Pick a .txt/.md file, choose a preset or cloned voice, and convert it to a
.wav file. All heavy work runs on a background thread so the window stays
responsive; messages flow back to the UI through a thread-safe queue.
"""

from __future__ import annotations

import os
import queue
import sys
import threading
import traceback
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import __version__
from .engine import PRESET_SPEAKERS, TTSEngine, save_wav
from .textio import load_text, read_plain, split_into_chunks

# Languages supported by Qwen3-TTS (English is the default).
LANGUAGES = [
    "English", "Chinese", "German", "Italian", "Portuguese",
    "Spanish", "Japanese", "Korean", "French", "Russian",
]

TEXT_FILETYPES = [("Text & Markdown", "*.txt *.md *.markdown *.text"),
                  ("All files", "*.*")]
AUDIO_FILETYPES = [("Audio files", "*.wav *.mp3 *.flac *.ogg *.m4a"),
                   ("All files", "*.*")]


class ConverterApp:
    """The main application window."""

    def __init__(self, root: tk.Tk, initial_file: str | None = None):
        self.root = root
        self.events: queue.Queue = queue.Queue()
        self.engine = TTSEngine(log=self._log_from_thread)
        self.busy = False

        root.title(f"Qwen3-TTS Converter v{__version__}")
        root.minsize(620, 580)

        self._build_ui()
        self._on_mode_change()
        if initial_file:
            self._set_input(initial_file)

        root.after(120, self._drain_events)

    # -- UI construction --------------------------------------------------
    def _build_ui(self) -> None:
        pad = {"padx": 10, "pady": 6}
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=1)

        # Input file
        in_frame = ttk.LabelFrame(main, text="Input file  (.txt or .md)")
        in_frame.grid(row=0, column=0, sticky="ew", **pad)
        in_frame.columnconfigure(0, weight=1)
        self.input_var = tk.StringVar()
        ttk.Entry(in_frame, textvariable=self.input_var, state="readonly").grid(
            row=0, column=0, sticky="ew", padx=8, pady=8)
        ttk.Button(in_frame, text="Browse...", command=self._choose_input).grid(
            row=0, column=1, padx=8, pady=8)

        # Voice settings
        voice = ttk.LabelFrame(main, text="Voice")
        voice.grid(row=1, column=0, sticky="ew", **pad)
        voice.columnconfigure(1, weight=1)

        self.mode_var = tk.StringVar(value="preset")
        ttk.Radiobutton(voice, text="Preset voice", value="preset",
                        variable=self.mode_var, command=self._on_mode_change
                        ).grid(row=0, column=0, sticky="w", padx=8, pady=4)
        ttk.Radiobutton(voice, text="Clone a voice", value="clone",
                        variable=self.mode_var, command=self._on_mode_change
                        ).grid(row=0, column=1, sticky="w", padx=8, pady=4)

        # Preset speaker
        self.preset_label = ttk.Label(voice, text="Speaker:")
        self.preset_label.grid(row=1, column=0, sticky="w", padx=8, pady=4)
        self.speaker_var = tk.StringVar(value=PRESET_SPEAKERS[0])
        self.speaker_combo = ttk.Combobox(
            voice, textvariable=self.speaker_var, values=PRESET_SPEAKERS,
            state="readonly", width=20)
        self.speaker_combo.grid(row=1, column=1, sticky="w", padx=8, pady=4)

        # Clone: reference audio
        self.ref_audio_label = ttk.Label(voice, text="Reference audio:")
        self.ref_audio_label.grid(row=2, column=0, sticky="w", padx=8, pady=4)
        self.ref_audio_var = tk.StringVar()
        self.ref_audio_entry = ttk.Entry(voice, textvariable=self.ref_audio_var,
                                         state="readonly")
        self.ref_audio_entry.grid(row=2, column=1, sticky="ew", padx=8, pady=4)
        self.ref_audio_btn = ttk.Button(voice, text="Browse...",
                                        command=self._choose_ref_audio)
        self.ref_audio_btn.grid(row=2, column=2, padx=8, pady=4)

        # Clone: reference transcript
        self.ref_text_label = ttk.Label(voice, text="Reference transcript:")
        self.ref_text_label.grid(row=3, column=0, sticky="w", padx=8, pady=4)
        self.ref_text_var = tk.StringVar()
        self.ref_text_entry = ttk.Entry(voice, textvariable=self.ref_text_var,
                                        state="readonly")
        self.ref_text_entry.grid(row=3, column=1, sticky="ew", padx=8, pady=4)
        self.ref_text_btn = ttk.Button(voice, text="Browse...",
                                       command=self._choose_ref_text)
        self.ref_text_btn.grid(row=3, column=2, padx=8, pady=4)

        # Language
        ttk.Label(voice, text="Language:").grid(row=4, column=0, sticky="w",
                                                padx=8, pady=4)
        self.language_var = tk.StringVar(value=LANGUAGES[0])
        ttk.Combobox(voice, textvariable=self.language_var, values=LANGUAGES,
                     state="readonly", width=20).grid(row=4, column=1,
                                                      sticky="w", padx=8, pady=4)

        # Output file
        out_frame = ttk.LabelFrame(main, text="Output file  (.wav)")
        out_frame.grid(row=2, column=0, sticky="ew", **pad)
        out_frame.columnconfigure(0, weight=1)
        self.output_var = tk.StringVar()
        ttk.Entry(out_frame, textvariable=self.output_var).grid(
            row=0, column=0, sticky="ew", padx=8, pady=8)
        ttk.Button(out_frame, text="Save as...", command=self._choose_output
                   ).grid(row=0, column=1, padx=8, pady=8)

        # Convert button + progress
        action = ttk.Frame(main)
        action.grid(row=3, column=0, sticky="ew", **pad)
        action.columnconfigure(0, weight=1)
        self.progress = ttk.Progressbar(action, mode="determinate")
        self.progress.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.convert_btn = ttk.Button(action, text="Convert",
                                      command=self._start_conversion)
        self.convert_btn.grid(row=0, column=1)

        # Log
        log_frame = ttk.LabelFrame(main, text="Status")
        log_frame.grid(row=4, column=0, sticky="nsew", **pad)
        main.rowconfigure(4, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log = tk.Text(log_frame, height=10, wrap="word", state="disabled")
        self.log.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=8)
        scroll = ttk.Scrollbar(log_frame, command=self.log.yview)
        scroll.grid(row=0, column=1, sticky="ns", pady=8)
        self.log.configure(yscrollcommand=scroll.set)

        self._log("Choose a .txt or .md file, pick a voice, then Convert.")
        self._log("Tip: the first conversion downloads the model (~1.2 GB).")

    # -- file pickers -----------------------------------------------------
    def _choose_input(self) -> None:
        path = filedialog.askopenfilename(title="Choose a text file",
                                          filetypes=TEXT_FILETYPES)
        if path:
            self._set_input(path)

    def _set_input(self, path: str) -> None:
        self.input_var.set(path)
        stem, _ = os.path.splitext(path)
        self.output_var.set(stem + ".wav")

    def _choose_ref_audio(self) -> None:
        path = filedialog.askopenfilename(title="Choose reference audio",
                                          filetypes=AUDIO_FILETYPES)
        if path:
            self.ref_audio_var.set(path)

    def _choose_ref_text(self) -> None:
        path = filedialog.askopenfilename(title="Choose reference transcript",
                                          filetypes=TEXT_FILETYPES)
        if path:
            self.ref_text_var.set(path)

    def _choose_output(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Save audio as", defaultextension=".wav",
            filetypes=[("WAV audio", "*.wav")])
        if path:
            self.output_var.set(path)

    # -- mode toggling ----------------------------------------------------
    def _on_mode_change(self) -> None:
        preset = self.mode_var.get() == "preset"
        preset_state = "readonly" if preset else "disabled"
        clone_state = "disabled" if preset else "!disabled"

        self.speaker_combo.configure(state=preset_state)
        self.preset_label.configure(
            foreground="" if preset else "gray")
        for widget in (self.ref_audio_entry, self.ref_text_entry):
            widget.configure(state="readonly" if not preset else "disabled")
        for widget in (self.ref_audio_btn, self.ref_text_btn):
            widget.state(["!disabled"] if not preset else ["disabled"])
        for label in (self.ref_audio_label, self.ref_text_label):
            label.configure(foreground="" if not preset else "gray")

    # -- conversion -------------------------------------------------------
    def _start_conversion(self) -> None:
        if self.busy:
            return

        try:
            params = self._collect_params()
        except ValueError as exc:
            messagebox.showwarning("Missing information", str(exc))
            return

        self.busy = True
        self.convert_btn.configure(state="disabled")
        self.progress.configure(mode="indeterminate")
        self.progress.start(12)
        self._log("\n--- Conversion started ---")

        worker = threading.Thread(target=self._run_worker, args=(params,),
                                  daemon=True)
        worker.start()

    def _collect_params(self) -> dict:
        input_path = self.input_var.get().strip()
        output_path = self.output_var.get().strip()
        if not input_path:
            raise ValueError("Please choose an input .txt or .md file.")
        if not os.path.isfile(input_path):
            raise ValueError(f"Input file not found:\n{input_path}")
        if not output_path:
            raise ValueError("Please choose where to save the output .wav file.")

        mode = self.mode_var.get()
        params = {
            "input": input_path,
            "output": output_path,
            "mode": mode,
            "language": self.language_var.get(),
            "speaker": self.speaker_var.get(),
            "ref_audio": None,
            "ref_text_path": None,
        }

        if mode == "clone":
            ref_audio = self.ref_audio_var.get().strip()
            ref_text = self.ref_text_var.get().strip()
            if not ref_audio or not os.path.isfile(ref_audio):
                raise ValueError("Please choose a valid reference audio file.")
            if not ref_text or not os.path.isfile(ref_text):
                raise ValueError(
                    "Please choose the transcript of the reference audio.")
            params["ref_audio"] = ref_audio
            params["ref_text_path"] = ref_text

        return params

    def _run_worker(self, params: dict) -> None:
        """Background thread: load text, synthesize, save. Never touches Tk."""
        try:
            self._post("log", "Reading input file...")
            text = load_text(params["input"])
            chunks = split_into_chunks(text)
            self._post("log", f"Text prepared: {len(text)} characters, "
                              f"{len(chunks)} chunk(s).")

            ref_text = None
            if params["mode"] == "clone":
                ref_text = read_plain(params["ref_text_path"])

            def progress(index: int, total: int, chunk: str) -> None:
                self._post("progress", index, total)
                self._post("log",
                           f"  Synthesizing chunk {index}/{total} "
                           f"({len(chunk)} chars)...")

            audio, sample_rate = self.engine.convert(
                chunks,
                mode=params["mode"],
                language=params["language"],
                speaker=params["speaker"],
                ref_audio=params["ref_audio"],
                ref_text=ref_text,
                progress=progress,
            )

            self._post("log", "Saving audio file...")
            save_wav(params["output"], audio, sample_rate)
            duration = len(audio) / sample_rate
            self._post("done", params["output"], duration)

        except Exception as exc:  # noqa: BLE001 -- surfaced to the user
            self._post("error", str(exc), traceback.format_exc())

    # -- thread-safe messaging -------------------------------------------
    def _post(self, *event) -> None:
        self.events.put(event)

    def _log_from_thread(self, message: str) -> None:
        self._post("log", message)

    def _drain_events(self) -> None:
        try:
            while True:
                event = self.events.get_nowait()
                self._handle_event(event)
        except queue.Empty:
            pass
        self.root.after(120, self._drain_events)

    def _handle_event(self, event: tuple) -> None:
        kind = event[0]
        if kind == "log":
            self._log(event[1])
        elif kind == "progress":
            index, total = event[1], event[2]
            if self.progress["mode"] != "determinate":
                self.progress.stop()
                self.progress.configure(mode="determinate", maximum=total)
            self.progress["value"] = index
        elif kind == "done":
            self._finish_success(event[1], event[2])
        elif kind == "error":
            self._finish_error(event[1], event[2])

    def _finish_success(self, output_path: str, duration: float) -> None:
        self.progress.stop()
        self.progress.configure(mode="determinate")
        self.progress["value"] = self.progress["maximum"]
        self._log(f"Done. Saved {duration:.1f}s of audio to:\n{output_path}")
        self.busy = False
        self.convert_btn.configure(state="normal")
        messagebox.showinfo("Conversion complete",
                            f"Audio saved to:\n{output_path}")

    def _finish_error(self, message: str, detail: str) -> None:
        self.progress.stop()
        self.progress.configure(mode="determinate")
        self.progress["value"] = 0
        self._log(f"ERROR: {message}")
        self._log(detail)
        self.busy = False
        self.convert_btn.configure(state="normal")
        messagebox.showerror("Conversion failed", message)

    def _log(self, message: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", message.rstrip() + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")


def main() -> None:
    """Entry point: launch the GUI, optionally pre-loading a file from argv."""
    initial_file = None
    for arg in sys.argv[1:]:
        if os.path.isfile(arg):
            initial_file = arg
            break

    root = tk.Tk()
    ConverterApp(root, initial_file)
    root.mainloop()


if __name__ == "__main__":
    main()
