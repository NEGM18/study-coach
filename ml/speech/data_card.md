# Data card — speech (Model B)

| Field | Value |
| --- | --- |
| Owner(s) | Omar Negm (pipeline), Fares (recordings, corrections) |
| Sources (link, license, download date) | MGB-3 Egyptian Arabic (QCRI, research licence, **access requested — issue #7**); ArzEn code-switched Egyptian Arabic/English (research licence, **access requested — issue #7**); Common Voice Arabic (CC0, needs a Mozilla account download); our lectures recorded with professor permission (issue #8). |
| Final dataset file(s) | `ml/data/processed/speech/speech_train_v1.jsonl`, `speech_dev_v1.jsonl`, `speech_test_v1.jsonl` |
| Rows / hours | **Not built yet**: no source audio is in DVC. Re-run the build once MGB-3/ArzEn access and the recordings arrive. |
| Splits | Public data -> train only; our corrected lectures -> dev/test by lecture (`dev_fraction_of_ours: 0.5`) |
| Split rule | By lecture for our data; any public clip whose speaker is also in dev/test is dropped (`ml_core.speech.clean.speaker_safe_split`) |
| Manifest row | audio_path, start_s, end_s, text (`normalize_for_training`), speaker_id (professors are P1, P2, …), lecture_id, source |

Pipeline, all thresholds in `ml/speech/configs/build.yaml`:
1. `ml_core.speech.audio.prepare_audio`: 16 kHz mono FLAC, EBU R128 loudness, VAD clips of 1-30 s (issue #2, merged).
2. `ml.speech.scripts.draft_transcripts` (Colab GPU): Whisper large-v3 drafts -> `speech_pseudo_v1.jsonl` for Fares (issue #3); Whisper-small zero-shot drafts for the CER filter (issue #5).
3. `ml.speech.scripts.build_dataset`: convert sources, then the steps below, then the splits (issues #4, #5).

## Cleaning steps (`ml/speech/cleaning_log.csv`: rows **and hours** in/out per step)

| Step | Rule |
| --- | --- |
| duration | drop clips < 1 s or > 30 s |
| text | `normalize_for_training`, then drop empty text |
| alignment | drop clips with < 2 or > 30 non-space characters per second |
| quality | drop *public* clips whose zero-shot Whisper-small CER is > 0.8 (our lectures are never dropped here) |

## Contract

`ml_core.speech.predict.transcribe(audio_path) -> list[Segment]`: VAD clips, each sent to Gemini (`GEMINI_API_KEY`, model from `GEMINI_MODEL`, default `gemini-2.5-flash`). Without a key it returns the ordered speech segments with empty text, so the contract test runs in CI.

## Known issues

- Blocked on data: MGB-3 / ArzEn licences (issue #7), lecture recordings (#8) and Fares' corrections (#9, #10).
- Common Voice is read-speech MSA, not lecture dialect; it is train-only filler.
