"""Issue #3 (and the zero-shot CER filter in #5): Whisper drafts for every clip.

Run on a Colab GPU after `uv sync --extra speech --extra asr`:
  python -m ml.speech.scripts.draft_transcripts --clips ml/data/interim/speech/clips \
      --model openai/whisper-large-v3 --out ml/data/interim/speech/speech_pseudo_v1.jsonl
For the CER filter use --model openai/whisper-small and --out .../whisper_small_zero_shot_v1.jsonl.
Writes one JSON row per clip: audio_path, start_s, end_s, text (normalize_for_training).
"""

import argparse
import json
import logging
from pathlib import Path

import soundfile as sf

from ml_core.text_normalize import normalize_for_training

LOGGER = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clips", required=True, help="folder of *_segNNNN.flac clips from prepare_audio")
    parser.add_argument("--model", default="openai/whisper-large-v3")
    parser.add_argument("--out", required=True)
    parser.add_argument("--language", default="ar")
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    import torch
    from transformers import pipeline

    has_gpu = torch.cuda.is_available()
    asr = pipeline(
        "automatic-speech-recognition",
        model=args.model,
        torch_dtype=torch.float16 if has_gpu else torch.float32,
        device=0 if has_gpu else -1,
    )
    clips = sorted(Path(args.clips).rglob("*.flac"))
    results = asr(
        [str(p) for p in clips],
        batch_size=args.batch_size,
        generate_kwargs={"language": args.language, "task": "transcribe"},
    )
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        for path, result in zip(clips, results, strict=True):
            row = {
                "audio_path": str(path),
                "start_s": 0.0,
                "end_s": sf.info(path).duration,
                "text": normalize_for_training(result["text"]),
            }
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    LOGGER.info("wrote %d drafts with %s to %s", len(clips), args.model, args.out)


if __name__ == "__main__":
    main()
