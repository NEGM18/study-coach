"""Model B contract. Owner: Omar Negm (issue #5).

Week 1 stub: Gemini audio transcription per VAD clip.
The fine-tuned Whisper replaces it later; Gemini stays as the fallback.
Without GEMINI_API_KEY (CI, offline) it returns the speech segments with empty text.
"""

import base64
import io
import json
import logging
import os
import re
import urllib.request

import numpy as np
import soundfile as sf

from ml_core.schemas import Segment
from ml_core.speech.audio import (
    MAX_CLIP_SECONDS,
    MIN_CLIP_SECONDS,
    TARGET_SAMPLE_RATE,
    detect_speech,
    load_audio,
    merge_short_spans,
    normalize_loudness,
    split_long_spans,
)
from ml_core.text_normalize import normalize_for_training

LOGGER = logging.getLogger(__name__)
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
PROMPT = (
    "Transcribe this Egyptian university lecture clip verbatim. Write Arabic words in Arabic script "
    "and English words in Latin script, exactly as spoken. Do not translate, correct grammar or convert "
    "dialect to MSA. Return only the transcript, or nothing if there is no speech."
)


def transcribe(audio_path: str) -> list[Segment]:
    """Ordered, normalized segments for one recording."""
    samples = normalize_loudness(load_audio(audio_path))
    max_len = int(MAX_CLIP_SECONDS * TARGET_SAMPLE_RATE)
    min_len = int(MIN_CLIP_SECONDS * TARGET_SAMPLE_RATE)
    spans = merge_short_spans(split_long_spans(detect_speech(samples), max_len), min_len, max_len)
    api_key = os.environ.get("GEMINI_API_KEY", "")
    segments = []
    for start, end in spans:
        text = normalize_for_training(_gemini_text(samples[start:end], api_key)) if api_key else ""
        segments.append(
            Segment(
                start_s=start / TARGET_SAMPLE_RATE,
                end_s=end / TARGET_SAMPLE_RATE,
                text=text,
                has_english=bool(re.search(r"[a-z]", text)),
            )
        )
    LOGGER.info("%s: %d segments (gemini=%s)", audio_path, len(segments), bool(api_key))
    return segments


def _gemini_text(clip: np.ndarray, api_key: str) -> str:
    buffer = io.BytesIO()
    sf.write(buffer, clip, TARGET_SAMPLE_RATE, format="FLAC", subtype="PCM_16")
    audio = base64.b64encode(buffer.getvalue()).decode()
    body = {
        "contents": [
            {"parts": [{"text": PROMPT}, {"inline_data": {"mime_type": "audio/flac", "data": audio}}]}
        ]
    }
    model = os.environ.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
    request = urllib.request.Request(
        GEMINI_URL.format(model=model),
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.load(response)
    parts = payload.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    return " ".join(part.get("text", "") for part in parts).strip()
