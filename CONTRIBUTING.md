# Contributing

Every task is a GitHub issue, every change is a pull request, and nothing reaches `main` without review.

## Branches

- `main` = production. Week 1: all data work merges here through reviewed PRs.
- `dev` = staging, created in Week 2 when app code starts. Full deployment rules: README section 5.
- Work branches start from the latest `main`: `data/<model>-<task>` (Week 1) or `feature/<issue>-<short-name>` / `fix/<issue>-<short-name>` (from Week 2).

## Commits

Conventional Commits: `feat(knowledge): add topic-agnostic features`, `fix(topics): keep slide titles during header removal`, `test(speech): VAD edge cases`, `docs: update data card`.

## Delivering a task

1. Move your issue to **In progress** on the board.
2. `git checkout main && git pull && git checkout -b data/<model>-<task>`
3. Build it, run it, add or update tests.
4. `uv run pytest && uv run ruff check . && uv run ruff format --check .`
5. Open a PR into `main` with the template; link the issue (`Closes #12`).
6. Reviewer approves or requests changes within 24 hours.
7. Squash-merge and close the issue with proof: counts from `cleaning_log.csv`, a screenshot or 5 sample rows.

## Reviews

- Omar Negm reviews every PR; Amr reviews Omar's.
- Fares and Hager: ask your pair lead for a first look before requesting Omar.
- Keep PRs under about 400 changed lines; split bigger work.
- Reviewers check: it works, follows `CLAUDE.md`, has tests, no secrets or raw data.

## Definition of Done

- [ ] Merged into `main` with CI green
- [ ] Tests added or updated
- [ ] Data (if any) pushed to DVC, `.dvc` file committed
- [ ] Data card updated if the dataset changed
- [ ] Issue closed with proof

## Getting help

Daily async standup in the team chat by 10 pm: done, next, blocked. Stuck for more than an hour after two or three different prompts? Post in the chat instead of looping.
