# Database (Supabase Postgres)

- `migrations/NNNN_description.sql`: applied in order, once per environment. Never edit an applied file; add the next number.
- `seed/course_topics_seed.sql`: generated from `seed/course_topics_seed.json` (3 courses, 39 topics); safe to re-run.
- `ml_core/tests/test_schemas.py` checks that every `ml_core/schemas.py` field is a column in the migrations.

## Applied

| Environment | Supabase project | Applied | Date |
| --- | --- | --- | --- |
| dev | `study-coach-dev` (eu-west-1) | 0001, 0002, seed | 2026-11-19 |
| staging | not created yet (#39) | — | — |
| production | not created yet | — | — |

Update this table in the PR that applies a migration.

## How to apply

Supabase dashboard -> SQL Editor: paste each new migration in order, then the seed. Or with psql and the
project's connection string (kept out of Git):

```bash
psql "$SUPABASE_DB_URL" -v ON_ERROR_STOP=1 -f db/migrations/0001_init.sql
psql "$SUPABASE_DB_URL" -v ON_ERROR_STOP=1 -f db/migrations/0002_harden_functions.sql
psql "$SUPABASE_DB_URL" -v ON_ERROR_STOP=1 -f db/seed/course_topics_seed.sql
```

Afterwards, check Dashboard -> Advisors -> Security shows no warnings.

## Access model

- The app holds only the URL and the **anon** key; Row Level Security decides what each student sees:
  their own `users`, `quiz_attempts`, `topic_mastery` and `jobs` rows, and a course's topics, lectures,
  chunks and questions only after joining it (`course_members`). The course catalog is readable when signed in.
- The API and worker use the **service-role** key (server only, never in the app); it bypasses RLS to write
  lectures, chunks, jobs and `topic_mastery`.
- A new sign-up gets a `users` row automatically (trigger on `auth.users`).
