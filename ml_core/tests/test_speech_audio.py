"""Model B audio preparation: decoding, loudness, VAD clips and the clip-length rules."""

import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

audio = pytest.importorskip("ml_core.speech.audio", reason="needs the speech extra: uv sync --extra speech")
librosa = pytest.importorskip("librosa")
pyloudnorm = pytest.importorskip("pyloudnorm")
sf = pytest.importorskip("soundfile")

FIXTURE = Path(__file__).parents[2] / "tests" / "fixtures" / "speech_sample_01.flac"
RATE = audio.TARGET_SAMPLE_RATE


def tone(seconds: float, rate: int, amplitude: float) -> np.ndarray:
    t = np.arange(int(seconds * rate)) / rate
    return (amplitude * np.sin(2 * np.pi * 440 * t)).astype(np.float32)


def assert_valid_clips(clips: list, max_end_s: float) -> None:
    assert clips
    for clip in clips:
        info = sf.info(clip.path)
        assert (info.format, info.samplerate, info.channels) == ("FLAC", RATE, 1)
        assert audio.MIN_CLIP_SECONDS <= clip.end_s - clip.start_s <= audio.MAX_CLIP_SECONDS
        assert info.frames == round((clip.end_s - clip.start_s) * RATE)
    assert all(a.end_s <= b.start_s for a, b in zip(clips, clips[1:], strict=False))
    assert 0 <= clips[0].start_s and clips[-1].end_s <= max_end_s


def test_split_long_spans_cuts_only_long_spans_into_equal_parts() -> None:
    spans = [(0, 100), (200, 270), (300, 330)]

    assert audio.split_long_spans(spans, max_len=30) == [
        (0, 25),
        (25, 50),
        (50, 75),
        (75, 100),
        (200, 223),
        (223, 246),
        (246, 270),
        (300, 330),
    ]


def test_merge_short_spans_joins_short_piece_into_previous() -> None:
    assert audio.merge_short_spans([(0, 50), (60, 65), (100, 150)], min_len=10, max_len=100) == [
        (0, 65),
        (100, 150),
    ]


def test_merge_short_spans_joins_leading_short_piece_into_next() -> None:
    assert audio.merge_short_spans([(0, 5), (10, 50)], min_len=10, max_len=100) == [(0, 50)]


def test_merge_short_spans_drops_short_piece_when_no_neighbour_fits() -> None:
    merged = audio.merge_short_spans([(0, 95), (150, 155), (200, 290)], min_len=10, max_len=100)

    assert merged == [(0, 95), (200, 290)]


def test_merge_short_spans_handles_no_speech() -> None:
    assert audio.merge_short_spans([], min_len=10, max_len=100) == []


def test_clip_stem_drops_recording_date() -> None:
    assert audio.clip_stem("ml/data/raw/speech/ds_lec03_20261102.m4a") == "ds_lec03"
    assert audio.clip_stem("upload_7.wav") == "upload_7"


def test_load_audio_converts_stereo_44k_wav_to_16k_mono(tmp_path: Path) -> None:
    path = tmp_path / "stereo.wav"
    wave = tone(2.0, 44_100, 0.5)
    sf.write(path, np.stack([wave, wave], axis=1), 44_100)

    samples = audio.load_audio(str(path))

    assert samples.ndim == 1 and samples.dtype == np.float32
    assert abs(len(samples) - 2 * RATE) <= 1


def test_load_audio_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        audio.load_audio(str(tmp_path / "missing.wav"))


def test_load_audio_asks_for_ffmpeg_when_format_is_unreadable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "phone.m4a"
    path.write_bytes(b"\x00\x00\x00\x18ftypM4A " + bytes(200))
    monkeypatch.setattr(audio.shutil, "which", lambda name: None)

    with pytest.raises(RuntimeError, match="ffmpeg"):
        audio.load_audio(str(path))


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not on PATH")
def test_load_audio_decodes_m4a_with_ffmpeg(tmp_path: Path) -> None:
    wav, m4a = tmp_path / "source.wav", tmp_path / "phone.m4a"
    sf.write(wav, tone(2.0, 44_100, 0.5), 44_100)
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-c:a", "aac", str(m4a)], check=True)

    samples = audio.load_audio(str(m4a))

    assert samples.ndim == 1 and samples.dtype == np.float32
    assert abs(len(samples) - 2 * RATE) <= 0.1 * RATE


def test_normalize_loudness_reaches_target() -> None:
    normalized = audio.normalize_loudness(tone(3.0, RATE, 0.01))

    assert normalized.dtype == np.float32
    assert pyloudnorm.Meter(RATE).integrated_loudness(normalized) == pytest.approx(audio.TARGET_LUFS, abs=0.5)


def test_normalize_loudness_keeps_peaks_under_limit() -> None:
    samples = tone(3.0, RATE, 0.01)
    samples[1000] = 0.5

    assert np.max(np.abs(audio.normalize_loudness(samples))) <= audio.PEAK_LIMIT + 1e-6


@pytest.mark.parametrize("samples", [np.zeros(2 * RATE, dtype=np.float32), tone(0.2, RATE, 0.5)])
def test_normalize_loudness_leaves_silence_and_very_short_audio_unchanged(samples: np.ndarray) -> None:
    np.testing.assert_array_equal(audio.normalize_loudness(samples), samples)


def test_prepare_audio_writes_16k_mono_flac_clips_for_fixture(tmp_path: Path) -> None:
    clips = audio.prepare_audio(str(FIXTURE), str(tmp_path / "clips"))

    assert_valid_clips(clips, max_end_s=sf.info(FIXTURE).duration)
    names = [Path(clip.path).name for clip in clips]
    assert names == [f"speech_sample_01_seg{index:04d}.flac" for index in range(len(clips))]


def test_prepare_audio_accepts_stereo_44k_wav(tmp_path: Path) -> None:
    samples, rate = sf.read(FIXTURE, dtype="float32")
    resampled = librosa.resample(samples, orig_sr=rate, target_sr=44_100)
    path = tmp_path / "ds_lec01_20261102.wav"
    sf.write(path, np.stack([resampled, resampled], axis=1), 44_100)

    clips = audio.prepare_audio(str(path), str(tmp_path / "clips"))

    assert_valid_clips(clips, max_end_s=len(resampled) / 44_100)
    assert Path(clips[0].path).name == "ds_lec01_seg0000.flac"


def test_prepare_audio_cuts_long_speech_into_clips_of_at_most_30_s(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "long.flac"
    sf.write(path, np.random.default_rng(42).normal(0, 0.05, 70 * RATE).astype(np.float32), RATE)
    monkeypatch.setattr(audio, "detect_speech", lambda samples: [(0, len(samples))])

    clips = audio.prepare_audio(str(path), str(tmp_path / "clips"))

    assert len(clips) == 3
    assert_valid_clips(clips, max_end_s=70.0)
    assert clips[0].start_s == 0.0 and clips[-1].end_s == 70.0


def test_prepare_audio_returns_no_clips_for_silence(tmp_path: Path) -> None:
    path = tmp_path / "silence.flac"
    sf.write(path, np.zeros(3 * RATE, dtype=np.float32), RATE)

    assert audio.prepare_audio(str(path), str(tmp_path / "clips")) == []
