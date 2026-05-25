"""Reading and preparing text input for synthesis.

Supports plain-text (.txt) and Markdown (.md) files. Markdown is reduced to
plain prose so formatting characters are not read aloud. Long text is split
into sentence-sized chunks the TTS model can handle one at a time.
"""

from __future__ import annotations

import os
import re

SUPPORTED_EXTENSIONS = (".txt", ".md", ".markdown", ".text")

# Roughly how many characters to feed the model per generation call. Keeping
# chunks modest gives steady progress updates and avoids very long generations.
DEFAULT_MAX_CHARS = 350

# Split on sentence-ending punctuation (Latin + CJK) followed by whitespace.
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?。！？])\s+")


def strip_markdown(md: str) -> str:
    """Convert Markdown source into plain prose suitable for speech."""
    text = md

    # Drop fenced code-block delimiters but keep the inner lines.
    text = re.sub(r"^[ \t]*(```|~~~).*$", "", text, flags=re.MULTILINE)

    # Images -> alt text; links -> link text.
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\[[^\]]*\]", r"\1", text)

    # Headings, blockquotes.
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s{0,3}>\s?", "", text, flags=re.MULTILINE)

    # Horizontal rules (--- *** ___) -- before emphasis stripping.
    text = re.sub(r"^\s{0,3}([-*_])\s?(\1\s?){2,}$", "", text, flags=re.MULTILINE)

    # List markers.
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+[.)]\s+", "", text, flags=re.MULTILINE)

    # Table separator rows, then turn remaining pipes into spaces.
    text = re.sub(r"^\s*\|?[\s:|-]+\|?\s*$", "", text, flags=re.MULTILINE)
    text = text.replace("|", " ")

    # Inline code, emphasis markers, raw HTML tags.
    text = text.replace("`", "")
    text = re.sub(r"(\*\*\*|\*\*|\*|___|__|_|~~)", "", text)
    text = re.sub(r"<[^>]+>", "", text)

    # Collapse runs of blank lines.
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def load_text(path: str) -> str:
    """Read a .txt/.md file and return cleaned, speakable text.

    Raises ValueError for unsupported extensions or empty files.
    """
    ext = os.path.splitext(path)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{ext or '(none)'}'. "
            "Please choose a .txt or .md file."
        )

    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        raw = fh.read()

    if ext in (".md", ".markdown"):
        raw = strip_markdown(raw)

    text = raw.strip()
    if not text:
        raise ValueError("The file contains no readable text.")
    return text


def read_plain(path: str) -> str:
    """Read a file as plain UTF-8 text (used for voice-clone transcripts)."""
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        text = fh.read().strip()
    if not text:
        raise ValueError(f"Transcript file is empty: {path}")
    return text


def split_into_chunks(text: str, max_chars: int = DEFAULT_MAX_CHARS) -> list[str]:
    """Split text into chunks no larger than ``max_chars``.

    Splits on blank-line paragraph breaks first, then on sentence
    boundaries, and finally on word boundaries for any oversized sentence.
    """
    chunks: list[str] = []

    for paragraph in re.split(r"\n\s*\n", text):
        paragraph = " ".join(paragraph.split())
        if not paragraph:
            continue
        if len(paragraph) <= max_chars:
            chunks.append(paragraph)
            continue

        current = ""
        for sentence in _SENTENCE_SPLIT.split(paragraph):
            sentence = sentence.strip()
            if not sentence:
                continue

            if len(sentence) > max_chars:
                # Sentence alone is too long: wrap on word boundaries.
                for word in sentence.split():
                    if len(current) + len(word) + 1 > max_chars and current:
                        chunks.append(current.strip())
                        current = word
                    else:
                        current = f"{current} {word}".strip()
            elif len(current) + len(sentence) + 1 > max_chars and current:
                chunks.append(current.strip())
                current = sentence
            else:
                current = f"{current} {sentence}".strip()

        if current.strip():
            chunks.append(current.strip())

    return chunks
