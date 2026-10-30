# Issue #11: shared DVC setup

Run every command below from the `study-coach` repository root using Python 3.12.
The existing `dev` extra includes DVC's Google Drive support, Ruff, and pytest.

## Shared configuration

The default remote is `shared_drive`, with URL
`gdrive://1LwuLmhOV_o-0l_HTf4n0b_f8pSOAsOgQ`. It uses the team's
[shared Google Drive folder](https://drive.google.com/drive/folders/1LwuLmhOV_o-0l_HTf4n0b_f8pSOAsOgQ).
The committed `.dvc/config` shares this configuration with every checkout.

Initialization commands already run for this issue:

```powershell
uv run dvc init
uv run dvc remote add -d shared_drive gdrive://1LwuLmhOV_o-0l_HTf4n0b_f8pSOAsOgQ
```

## Team setup message

Share this section in the team chat after the PR merges.

1. Grant every teammate's Google account explicit access to the shared folder;
   dataset uploaders need write access.
2. Use a team Google Cloud project with the Drive API enabled and a Desktop OAuth
   client. DVC's default Google OAuth client is affected by a Google block; see
   the [DVC Google Drive guide](https://doc.dvc.org/user-guide/data-management/remote-storage/google-drive).
   If the OAuth app is External and in Testing, add teammates as
   [test users](https://support.google.com/cloud/answer/15549945?hl=en).
3. Share the team's OAuth client credentials privately. Each teammate runs:

   ```powershell
   git pull
   uv sync --python 3.12 --extra dev
   uv run dvc remote list
   uv run dvc remote modify --local shared_drive gdrive_client_id "<team-client-id>"
   uv run dvc remote modify --local shared_drive gdrive_client_secret "<team-client-secret>"
   uv run dvc pull
   ```

4. When prompted, authenticate with the Google account that has folder access.
   DVC caches personal tokens locally. The `--local` options above go in
   Git-ignored `.dvc/config.local`; keep credentials and tokens private.
   See [DVC local configuration](https://doc.dvc.org/command-reference/remote/modify).
5. Once a dataset has been pushed, each teammate verifies a pull in a fresh
   checkout with an empty DVC cache, or pulls a newly tracked uncached dataset.
   Confirm that `uv run dvc pull` actually downloads objects, then report its
   result, Git commit, and tracked dataset path in chat as download proof.

## Publishing data later

When the first approved dataset is ready, its owner can track the whole data
directory and push it:

```powershell
uv run dvc add ml/data
uv run dvc push
git add ml/data.dvc
```

Commit the pointer through the normal reviewed PR workflow. `/ml/data/` is already
Git-ignored; `ml/data.dvc` sits outside that directory. Future changes to data
require updating the pointer and pushing the corresponding DVC objects before
teammates pull. Preserve the original files in `ml/data/raw/`.

## Verification and remaining proof

No data or pipelines are tracked yet. `uv run dvc pull` currently exits 0 with
`Everything is up to date.`, and `uv run dvc status` reports that no data or
pipelines are tracked. This does not exercise Drive authentication or prove
downloads work. A pushed dataset and authenticated downloads into an empty cache
are still needed; see [what DVC pull downloads](https://doc.dvc.org/command-reference/pull).

The local checks on Python 3.12.10 pass: `uv run ruff format` leaves 36 files
unchanged, `uv run ruff check` passes, and `uv run pytest` reports 14 passed and
4 expected failures for the existing model stubs. Thirteen passing cases cover
`CleaningLog`, including CSV round trips and row-count logging.

Schema contract confirmed: the project owner identifies `ml_core/schemas.py` as
the single source of truth for these three tables. It remains unchanged and
defines the following exact field names and types. `db/migrations/` and
`db/seed/` contain only empty `.gitkeep` files, so there are no competing table
definitions in this checkout:

| App table | Dataclass | Current fields and types |
| --- | --- | --- |
| `quiz_attempts` | `Attempt` | `user_id: str`, `topic_id: int`, `question_id: int`, `attempt_order: int`, `is_correct: bool`, `response_time_ms: int \| None = None`, `attempt_count: int = 1`, `hint_count: int = 0` |
| `lecture_chunks` | `Chunk` | `chunk_id: str`, `course_id: int`, `lecture_id: int`, `text: str`, `slide_no: int \| None = None`, `lang: Literal["ar", "en", "mixed"] = "ar"`, `topic_id: int \| None = None` |
| `course_topics` | `Topic` | `topic_id: int`, `course_id: int`, `name: str`, `description: str = ""` |

App tables and data-preparation code must use these names, types, nullability,
and defaults. Any future discrepancy requires approval before editing
`schemas.py`. Issue #11 still needs authenticated download proof from teammates,
Omar Negm's review, a merged PR with green CI, and issue closure with proof.
