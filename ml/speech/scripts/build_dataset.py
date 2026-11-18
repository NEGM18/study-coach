"""Build the model B dataset (issues #4, #5).

Converts MGB-3 / ArzEn (Kaldi folders) and Common Voice Arabic (TSV) to our JSONL
manifest, adds our corrected lectures, cleans with hours logged, drops public clips
with very high zero-shot CER, and writes speaker-safe train/dev/test splits.

Run: python -m ml.speech.scripts.build_dataset --config ml/speech/configs/build.yaml
"""

import argparse
import json
import logging
from pathlib import Path

import pandas as pd
import soundfile as sf
import yaml

from ml_core.speech.clean import MANIFEST_COLUMNS, HoursLog, clean_manifest, drop_high_cer, speaker_safe_split

LOGGER = logging.getLogger(__name__)


def _kaldi_table(path: Path, columns: int) -> list[list[str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [line.split(maxsplit=columns - 1) for line in lines if line.strip()]


def convert_kaldi(folder: Path, name: str) -> pd.DataFrame:
    """Kaldi data dir: text, segments (utt rec start end), wav.scp (rec path), utt2spk."""
    text = dict(_kaldi_table(folder / "text", 2))
    wavs = dict(_kaldi_table(folder / "wav.scp", 2))
    speakers = dict(_kaldi_table(folder / "utt2spk", 2))
    rows = [
        [wavs[rec], float(start), float(end), text.get(utt, ""), speakers.get(utt, rec), rec, name]
        for utt, rec, start, end in _kaldi_table(folder / "segments", 4)
    ]
    return pd.DataFrame(rows, columns=MANIFEST_COLUMNS)


def convert_common_voice(folder: Path, tsv: str, name: str) -> pd.DataFrame:
    """Common Voice: one clip per row; duration from the audio header."""
    table = pd.read_csv(folder / tsv, sep="\t", usecols=["client_id", "path", "sentence"], quoting=3)
    paths = [str(folder / "clips" / p) for p in table["path"]]
    return pd.DataFrame(
        {
            "audio_path": paths,
            "start_s": 0.0,
            "end_s": [sf.info(p).duration for p in paths],
            "text": table["sentence"],
            "speaker_id": table["client_id"],
            "lecture_id": table["path"],
            "source": name,
        }
    )


def load_sources(sources: list[dict]) -> pd.DataFrame:
    frames = []
    for source in sources:
        path = Path(source["path"])
        if not path.exists():
            LOGGER.warning(
                "skipping %s: %s not found (dvc pull, or access not granted yet)", source["name"], path
            )
            continue
        if source["format"] == "kaldi":
            frames.append(convert_kaldi(path, source["name"]))
        elif source["format"] == "common_voice":
            frames.append(convert_common_voice(path, source["tsv"], source["name"]))
        else:
            frames.append(pd.read_json(path, lines=True).assign(source="ours")[MANIFEST_COLUMNS])
        LOGGER.info("%s: %d clips", source["name"], len(frames[-1]))
    if not frames:
        raise SystemExit("no speech sources found; nothing to build")
    return pd.concat(frames, ignore_index=True)


def load_drafts(path: str) -> dict[str, str]:
    if not Path(path).exists():
        LOGGER.warning("no zero-shot drafts at %s; CER filter keeps every clip", path)
        return {}
    with open(path, encoding="utf-8") as handle:
        return {row["audio_path"]: row["text"] for row in map(json.loads, handle)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="ml/speech/configs/build.yaml")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))

    log = HoursLog("speech")
    clean = clean_manifest(load_sources(cfg["sources"]), cfg["cleaning"], log)
    clean = drop_high_cer(clean, load_drafts(cfg["cer_filter"]["drafts"]), cfg["cer_filter"]["max_cer"], log)
    split = speaker_safe_split(clean, cfg["splits"], cfg["seed"])

    out_dir = Path(cfg["output"]["dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in ("train", "dev", "test"):
        part = split[split["split"] == name].drop(columns="split")
        part.to_json(out_dir / cfg["output"][name], orient="records", lines=True, force_ascii=False)
        LOGGER.info("%s: %d clips, %.2f h", name, len(part), (part["end_s"] - part["start_s"]).sum() / 3600)
    log.to_frame().to_csv(cfg["output"]["cleaning_log"], index=False)


if __name__ == "__main__":
    main()
