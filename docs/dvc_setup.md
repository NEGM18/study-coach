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
   Set the OAuth app's publishing status to **In production**. In Testing,
   Google expires each login after 7 days, so everyone would have to sign in
   again every week. Because the app is unverified, each teammate sees a
   "Google hasn't verified this app" screen once: click **Advanced**, then
   continue.
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

## Publishing a dataset

Track **each dataset separately**, never the whole `ml/data` folder. One pointer
per dataset means pairs never edit the same file, and anyone can pull just the
data they need.

```powershell
# Example: Hager adds the raw Model A data
uv run dvc add ml/data/raw/knowledge
uv run dvc push
git add ml/data/raw/knowledge.dvc ml/data/raw/.gitignore
git commit -m "data(knowledge): add raw ASSISTments and EdNet"
```

| Model | Raw data | Processed data |
| --- | --- | --- |
| A — knowledge | `ml/data/raw/knowledge` | `ml/data/processed/knowledge` |
| B — speech | `ml/data/raw/speech` | `ml/data/processed/speech` |
| C — topics | `ml/data/raw/topics` | `ml/data/processed/topics` |

Commit the `.dvc` pointer through the normal reviewed PR workflow. The root
`.gitignore` hides every data file under `ml/data/` but keeps the `.dvc` pointers
and DVC's own `.gitignore` files visible to Git. When a dataset changes, run
`dvc add` and `dvc push` again before opening the PR, so teammates can pull it.
Never edit the original files in `ml/data/raw/`.

To download only one model's data: `uv run dvc pull ml/data/raw/knowledge.dvc`.

## Schema contract

`ml_core/schemas.py` is the single source of truth for these app tables. Data
and data-preparation code must use these exact field names and types:

| App table | Dataclass | Current fields and types |
| --- | --- | --- |
| `quiz_attempts` | `Attempt` | `user_id: str`, `topic_id: int`, `question_id: int`, `attempt_order: int`, `is_correct: bool`, `response_time_ms: int \| None = None`, `attempt_count: int = 1`, `hint_count: int = 0` |
| `lecture_chunks` | `Chunk` | `chunk_id: str`, `course_id: int`, `lecture_id: int`, `text: str`, `slide_no: int \| None = None`, `lang: Literal["ar", "en", "mixed"] = "ar"`, `topic_id: int \| None = None` |
| `course_topics` | `Topic` | `topic_id: int`, `course_id: int`, `name: str`, `description: str = ""` |

App tables and data-preparation code must use these names, types, nullability,
and defaults. Any change to `schemas.py` needs Omar's approval first.
