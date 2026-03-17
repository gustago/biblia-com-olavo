"""
Compat shim for the third-party `bangla` package.

The upstream `bangla` package versions pulled by `TTS` currently use Python 3.10+
type union syntax (e.g. `bool | None`), which breaks on Python 3.9 at import time.

`TTS` imports Bangla phonemizer modules unconditionally, even when you synthesize
Portuguese. To keep this project working on Python 3.9, we provide a tiny module
with the single function that the Bangla phonemizer references.

If/when you move to Python 3.10+, you can delete this file and rely on the real
dependency.
"""

from __future__ import annotations

__version__ = "shim"


def convert_english_digit_to_bangla_digit(text: str) -> str:
    # For non-Bangla use-cases (pt), returning the input is sufficient.
    return text

