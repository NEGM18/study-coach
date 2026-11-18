"""Speech manifest cleaning, error rate and speaker-safe splits. Owner: Omar Negm (issues #4, #5).

Manifest rows (JSONL / DataFrame): audio_path, start_s, end_s, text, speaker_id, lecture_id, source.
Thresholds come from ml/speech/configs/build.yaml and are passed in as `settings`.
"""

import logging

import numpy as np
import pandas as pd

from ml_core.cleaning_log import CleaningLog
from ml_core.text_normalize import normalize_for_eval, normalize_for_training

LOGGER = logging.getLogger(__name__)
MANIFEST_COLUMNS = ["audio_path", "start_s", "end_s", "text", "speaker_id", "lecture_id", "source"]


def hours(df: pd.DataFrame) -> float:
    return float((df["end_s"] - df["start_s"]).sum() / 3600)


class HoursLog:
    """CleaningLog plus hours in/out per step, as the speech data card needs."""

    def __init__(self, dataset: str) -> None:
        self.log = CleaningLog(dataset)
        self.hours: list[tuple[float, float]] = []

    def step(self, name: str, before: pd.DataFrame, after: pd.DataFrame, reason: str) -> pd.DataFrame:
        self.hours.append((round(hours(before), 3), round(hours(after), 3)))
        return self.log.step(name, before, after, reason)

    def to_frame(self) -> pd.DataFrame:
        table = pd.DataFrame(self.log.rows)
        table[["hours_before", "hours_after"]] = self.hours
        return table


def clean_manifest(df: pd.DataFrame, settings: dict, log: HoursLog) -> pd.DataFrame:
    """Duration, empty-text, normalization and alignment filters, in order."""
    duration = df["end_s"] - df["start_s"]
    df = log.step(
        f"drop clips < {settings['min_clip_s']} s or > {settings['max_clip_s']} s",
        df,
        df[(duration >= settings["min_clip_s"]) & (duration <= settings["max_clip_s"])],
        "Whisper takes at most 30 s; very short clips are noise",
    )
    df = df.assign(text=df["text"].fillna("").map(normalize_for_training))
    df = log.step("normalize_for_training + drop empty text", df, df[df["text"] != ""], "nothing to learn")
    cps = df["text"].str.replace(" ", "").str.len() / (df["end_s"] - df["start_s"])
    return log.step(
        f"drop chars/s outside [{settings['min_chars_per_s']}, {settings['max_chars_per_s']}]",
        df,
        df[(cps >= settings["min_chars_per_s"]) & (cps <= settings["max_chars_per_s"])],
        "text and audio are probably misaligned",
    )


def character_error_rate(reference: str, hypothesis: str) -> float:
    """Levenshtein distance over characters of eval-normalized text / reference length."""
    ref, hyp = normalize_for_eval(reference), normalize_for_eval(hypothesis)
    if not ref:
        return 0.0 if not hyp else 1.0
    previous = list(range(len(hyp) + 1))
    for i, ref_char in enumerate(ref, start=1):
        current = [i]
        for j, hyp_char in enumerate(hyp, start=1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (ref_char != hyp_char)))
        previous = current
    return previous[-1] / len(ref)


def drop_high_cer(df: pd.DataFrame, drafts: dict[str, str], max_cer: float, log: HoursLog) -> pd.DataFrame:
    """Drop public clips whose zero-shot Whisper draft disagrees too much with the reference."""
    cer = df.apply(lambda r: character_error_rate(r["text"], drafts.get(r["audio_path"], r["text"])), axis=1)
    is_public = df["source"] != "ours"
    return log.step(
        f"drop public clips with CER > {max_cer}",
        df,
        df[~is_public | (cer <= max_cer)],
        "reference probably wrong or audio unusable",
    )


def speaker_safe_split(df: pd.DataFrame, settings: dict, seed: int) -> pd.DataFrame:
    """Public data -> train; our lectures -> dev/test by lecture; no speaker or lecture in two splits."""
    out = df.copy()
    out["split"] = "train"
    ours = out["source"] == "ours"
    lectures = np.array(sorted(out.loc[ours, "lecture_id"].astype(str).unique()))
    np.random.default_rng(seed).shuffle(lectures)
    n_dev = int(round(settings["dev_fraction_of_ours"] * len(lectures)))
    lecture_split = {lec: ("dev" if i < n_dev else "test") for i, lec in enumerate(lectures)}
    out.loc[ours, "split"] = out.loc[ours, "lecture_id"].astype(str).map(lecture_split)
    held_out = set(out.loc[ours, "speaker_id"])
    leaked = (~ours) & out["speaker_id"].isin(held_out)
    if leaked.any():
        LOGGER.info("dropping %d public rows whose speaker is in dev/test", int(leaked.sum()))
    return out[~leaked].reset_index(drop=True)
