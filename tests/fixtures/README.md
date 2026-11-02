# Test fixtures

Small, anonymized files only: no real student, professor or lecture audio.

| File | What it is | Used by |
| --- | --- | --- |
| `speech_sample_01.flac` | 15.6 s of English speech made with Windows text-to-speech (Microsoft Zira), 16 kHz mono FLAC. Four sentences with pauses; one is a short "Okay." (about 0.6 s) to exercise merging of pieces under 1 s. | `ml_core/tests/test_speech_audio.py`, `ml_core/tests/test_contracts.py` |
