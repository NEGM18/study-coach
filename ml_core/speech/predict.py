"""Model B contract. Owner: Omar Negm (issue #5).

Week 1 stub: Gemini audio transcription per clip.
The fine-tuned Whisper replaces it later; Gemini stays as the fallback.
"""

from ml_core.schemas import Segment


def transcribe(audio_path: str) -> list[Segment]:
    raise NotImplementedError("Issue #5")
