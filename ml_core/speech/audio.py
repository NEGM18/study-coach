"""Audio preparation shared by training and the app. Owner: Omar Negm (issue #2).

16 kHz mono FLAC, loudness normalized, cut by voice activity (Silero VAD)
into clips of at most 30 s. Takes ONE file so the worker can call it per upload.
"""

from dataclasses import dataclass

TARGET_SAMPLE_RATE = 16_000
MAX_CLIP_SECONDS = 30.0
MIN_CLIP_SECONDS = 1.0


@dataclass(frozen=True)
class Clip:
    path: str
    start_s: float
    end_s: float


def prepare_audio(input_path: str, output_dir: str) -> list[Clip]:
    raise NotImplementedError("Issue #2")
