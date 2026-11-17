"""Audio preparation shared by training and the app. Owner: Omar Negm (issue #2).

16 kHz mono FLAC, loudness normalized, cut by voice activity (Silero VAD)
into clips of at most 30 s. Takes ONE file so the worker can call it per upload.
Formats libsndfile can't read (.m4a, .aac) are decoded with ffmpeg, which must be on PATH.
"""

import functools
import logging
import math
import re
import shutil
import subprocess
import warnings
from dataclasses import dataclass
from pathlib import Path

import librosa
import numpy as np
import pyloudnorm
import soundfile as sf
import torch
from silero_vad import get_speech_timestamps, load_silero_vad

LOGGER = logging.getLogger(__name__)

TARGET_SAMPLE_RATE = 16_000
MAX_CLIP_SECONDS = 30.0
MIN_CLIP_SECONDS = 1.0
TARGET_LUFS = -23.0  # EBU R128
PEAK_LIMIT = 0.99  # after loudness gain, scale down so no sample clips

type Span = tuple[int, int]  # [start, end) in samples


@dataclass(frozen=True)
class Clip:
    path: str
    start_s: float
    end_s: float


def prepare_audio(input_path: str, output_dir: str) -> list[Clip]:
    """Write one 16 kHz mono FLAC per speech clip of `input_path` into `output_dir`."""
    samples = normalize_loudness(load_audio(input_path))
    max_len = int(MAX_CLIP_SECONDS * TARGET_SAMPLE_RATE)
    min_len = int(MIN_CLIP_SECONDS * TARGET_SAMPLE_RATE)
    spans = merge_short_spans(split_long_spans(detect_speech(samples), max_len), min_len, max_len)

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = clip_stem(input_path)
    clips = []
    for index, (start, end) in enumerate(spans):
        path = out_dir / f"{stem}_seg{index:04d}.flac"
        sf.write(path, samples[start:end], TARGET_SAMPLE_RATE, format="FLAC", subtype="PCM_16")
        clips.append(Clip(str(path), start / TARGET_SAMPLE_RATE, end / TARGET_SAMPLE_RATE))
    LOGGER.info("%s: %.1f s -> %d clips", input_path, len(samples) / TARGET_SAMPLE_RATE, len(clips))
    return clips


def load_audio(input_path: str) -> np.ndarray:
    """Decode any audio file to 16 kHz mono float32 samples."""
    if not Path(input_path).is_file():
        raise FileNotFoundError(input_path)
    try:
        samples, sample_rate = sf.read(input_path, dtype="float32", always_2d=True)
    except sf.LibsndfileError:
        return _decode_with_ffmpeg(input_path)
    mono = samples.mean(axis=1)
    if sample_rate != TARGET_SAMPLE_RATE:
        mono = librosa.resample(mono, orig_sr=sample_rate, target_sr=TARGET_SAMPLE_RATE)
    return mono.astype(np.float32)


def _decode_with_ffmpeg(input_path: str) -> np.ndarray:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError(f"Can't decode {input_path}: install ffmpeg and put it on PATH")
    command = [ffmpeg, "-nostdin", "-v", "error", "-i", input_path]
    command += ["-ac", "1", "-ar", str(TARGET_SAMPLE_RATE), "-f", "f32le", "-"]
    result = subprocess.run(command, capture_output=True, check=False)
    if result.returncode != 0:
        error = result.stderr.decode(errors="replace").strip()
        raise RuntimeError(f"ffmpeg can't decode {input_path}: {error}")
    return np.frombuffer(result.stdout, dtype=np.float32).copy()


def normalize_loudness(samples: np.ndarray) -> np.ndarray:
    """Scale 16 kHz mono samples to TARGET_LUFS, then pull peaks under PEAK_LIMIT."""
    meter = pyloudnorm.Meter(TARGET_SAMPLE_RATE)
    try:
        loudness = meter.integrated_loudness(samples)
    except ValueError:  # shorter than one 400 ms measurement block
        return samples
    if not np.isfinite(loudness):  # silence
        return samples
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # pyloudnorm's clipping warning; the peak limit handles it
        normalized = pyloudnorm.normalize.loudness(samples, loudness, TARGET_LUFS)
    peak = float(np.max(np.abs(normalized)))
    if peak > PEAK_LIMIT:
        normalized = normalized * (PEAK_LIMIT / peak)
    return normalized.astype(np.float32)


@functools.cache
def _vad_model() -> torch.nn.Module:
    return load_silero_vad()


def detect_speech(samples: np.ndarray) -> list[Span]:
    """Speech regions found by Silero VAD in 16 kHz mono samples."""
    timestamps = get_speech_timestamps(
        torch.from_numpy(samples),
        _vad_model(),
        sampling_rate=TARGET_SAMPLE_RATE,
        max_speech_duration_s=MAX_CLIP_SECONDS,
    )
    return [(timestamp["start"], timestamp["end"]) for timestamp in timestamps]


def split_long_spans(spans: list[Span], max_len: int) -> list[Span]:
    """Cut every span longer than `max_len` into equal parts no longer than `max_len`."""
    result: list[Span] = []
    for start, end in spans:
        parts = math.ceil((end - start) / max_len)
        bounds = [start + (end - start) * part // parts for part in range(parts + 1)]
        result.extend(zip(bounds[:-1], bounds[1:], strict=True))
    return result


def merge_short_spans(spans: list[Span], min_len: int, max_len: int) -> list[Span]:
    """Join spans shorter than `min_len` to a neighbour while the joined span fits in `max_len`.

    A joined span keeps the pause between its pieces. Short spans that fit with no neighbour are dropped.
    """
    merged: list[Span] = []
    for start, end in spans:
        if merged:
            last_start, last_end = merged[-1]
            is_either_short = end - start < min_len or last_end - last_start < min_len
            if is_either_short and end - last_start <= max_len:
                merged[-1] = (last_start, end)
                continue
        merged.append((start, end))
    kept = [(start, end) for start, end in merged if end - start >= min_len]
    if len(kept) < len(merged):
        LOGGER.info("dropped %d speech pieces shorter than %d samples", len(merged) - len(kept), min_len)
    return kept


def clip_stem(input_path: str) -> str:
    """Clip file stem: the recording name without its date, so ds_lec03_20261102.m4a -> ds_lec03."""
    return re.sub(r"_\d{8}$", "", Path(input_path).stem)
