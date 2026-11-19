# Week 2 QA Checklist — AI Study Coach staging (W2-06, issue #40)

> [!IMPORTANT]
> **Prerequisites before running this checklist:**
> - W2-05 (staging: Supabase + Railway auto-deploy + smoke test) must be **green**.
> - W2-23 (Omar Mustafa's Flutter auth + courses + upload screens, staging test build) must be **distributed via Firebase App Distribution**.
> - Run on a real Android phone (not an emulator) in **both Arabic and English**.
> - The app build under test must be identified by version number (see below).

---

## Device & build info (fill in before each run)

| Field | Value |
| --- | --- |
| Tester name | |
| Test date | |
| App version (`pubspec.yaml`) | e.g. `0.2.0+5` |
| Build flavor | `staging` |
| Device model | e.g. Samsung Galaxy A54 |
| Android version | e.g. Android 14 |
| Network | Wi-Fi / Mobile data |
| App language under test | Arabic (AR) / English (EN) |
| Staging API base URL | `https://…railway.app/api/v1` |
| Staging Supabase project | `…supabase.co` |

---

## How to record results

For each step mark one of:
- ✅ **Pass** — behaves exactly as described
- ❌ **Fail** — does not behave as described; fill in the **Bug** column
- ⏭️ **Skip** — step not applicable (e.g. iOS-only step on Android)

File bugs as GitHub issues with: steps to reproduce, expected vs. actual, device info,
app version, screenshot or screen recording. Link the issue number in the **Bug** column.

---

## 0. Smoke test (before detailed QA)

| # | Step | Expected | AR ✓ | EN ✓ | Bug |
|---|------|----------|------|------|-----|
| 0.1 | Open the app cold | Splash screen appears; no crash within 3 s | | | |
| 0.2 | Health endpoint | `GET /api/v1/health` returns `200 OK` in < 2 s | | | |
| 0.3 | Layout direction | Arabic locale → entire app is RTL (text, icons, back arrow) | | | |
| 0.4 | Layout direction | English locale → entire app is LTR | | | |

---

## 1. Sign up

| # | Step | Expected | AR ✓ | EN ✓ | Bug |
|---|------|----------|------|------|-----|
| 1.1 | Tap "Sign up" on the welcome screen | Sign-up form opens (name, email, password) | | | |
| 1.2 | Submit with an empty email | Inline validation error shown below the email field; button stays disabled | | | |
| 1.3 | Submit with an invalid email format | Inline validation error; no network call | | | |
| 1.4 | Submit with a password shorter than 8 characters | Inline validation error; no network call | | | |
| 1.5 | Submit valid credentials | Account created; user lands on the home/course-list screen | | | |
| 1.6 | Try to sign up again with the same email | Error message: "email already in use" (or equivalent); no crash | | | |
| 1.7 | RTL check (AR only) | Form fields, labels and error messages are right-aligned and right-to-left | | | |

---

## 2. Log in

| # | Step | Expected | AR ✓ | EN ✓ | Bug |
|---|------|----------|------|------|-----|
| 2.1 | Tap "Log in" on the welcome screen | Login form opens (email, password) | | | |
| 2.2 | Submit with wrong password | Error: "Invalid credentials" (or equivalent); no crash; user stays on login screen | | | |
| 2.3 | Submit correct credentials | User lands on home/course-list screen; name or avatar shown | | | |
| 2.4 | Force-close app and reopen | User is still logged in (session persists) | | | |
| 2.5 | Log out | User is returned to the welcome screen; session cleared | | | |

---

## 3. Course selection / course list

| # | Step | Expected | AR ✓ | EN ✓ | Bug |
|---|------|----------|------|------|-----|
| 3.1 | View course list | At least one seeded course is listed (from `db/seed/course_topics_seed.sql`) | | | |
| 3.2 | Tap a course | Course detail / topic list opens | | | |
| 3.3 | Topic list not empty | At least one topic is shown for the selected course | | | |
| 3.4 | RTL check (AR only) | Course names and topics read right-to-left; list items start from the right | | | |
| 3.5 | Long course name | Does not overflow the card; text wraps or is ellipsised | | | |

---

## 4. Upload PDF lecture

> [!NOTE]
> This step requires the worker to be deployed on staging (`dev` → Railway auto-deploy).

| # | Step | Expected | AR ✓ | EN ✓ | Bug |
|---|------|----------|------|------|-----|
| 4.1 | Tap "Upload lecture" | File picker opens; PDF files selectable | | | |
| 4.2 | Select a PDF ≤ 50 MB | Upload progress indicator shown; upload completes | | | |
| 4.3 | Select a file > 50 MB | Error: "File too large"; no crash | | | |
| 4.4 | Select a non-PDF file | Error: "Unsupported file type"; no crash | | | |
| 4.5 | Upload completes | Lecture appears in the course's lecture list | | | |
| 4.6 | Worker processes the PDF | Within 60 s, lecture status changes from "processing" to "ready" | | | |

---

## 5. Upload audio lecture

> [!NOTE]
> Audio processing depends on the speech model (W2-14 / W2-15). Until the model is ready
> the worker calls the Gemini stub. Verify the stub path works end-to-end.

| # | Step | Expected | AR ✓ | EN ✓ | Bug |
|---|------|----------|------|------|-----|
| 5.1 | Tap "Upload lecture" and select an audio file (m4a / mp3 / flac) | Upload starts; progress shown | | | |
| 5.2 | File uploads successfully | Lecture appears in the list with status "processing" | | | |
| 5.3 | Worker transcribes (stub path) | Status changes to "ready"; at least one chunk is visible | | | |
| 5.4 | Arabic lecture audio | Transcript text is in Arabic; displayed RTL | | | |
| 5.5 | English lecture audio | Transcript text is in English; displayed LTR | | | |

---

## 6. Topic-tagged chunks

| # | Step | Expected | AR ✓ | EN ✓ | Bug |
|---|------|----------|------|------|-----|
| 6.1 | Open a processed lecture | List of chunks is shown (text snippets) | | | |
| 6.2 | Each chunk has a topic tag | Topic name is displayed next to or below each chunk | | | |
| 6.3 | Topic tag is from the course's topic list | Tapping the tag opens (or names) the matched course topic | | | |
| 6.4 | RTL check (AR only) | Chunk text and topic tags are right-aligned | | | |
| 6.5 | Long chunk text | Does not overflow; scrollable or truncated with "read more" | | | |

---

## 7. Quiz attempt

| # | Step | Expected | AR ✓ | EN ✓ | Bug |
|---|------|----------|------|------|-----|
| 7.1 | Start a quiz on a topic | Quiz screen opens with at least one question | | | |
| 7.2 | Answer a question | Option is highlighted; "Next" button enabled | | | |
| 7.3 | Submit all answers | Results screen shows correct/incorrect per question | | | |
| 7.4 | Results are persisted | Re-opening the quiz shows the previous attempt's score | | | |
| 7.5 | Arabic question text | Question and answers are right-to-left | | | |
| 7.6 | English question text | Question and answers are left-to-right | | | |
| 7.7 | Network lost mid-quiz | Graceful error shown; partial answers not silently lost | | | |

---

## 8. Mastery / topic readiness

| # | Step | Expected | AR ✓ | EN ✓ | Bug |
|---|------|----------|------|------|-----|
| 8.1 | View topic detail after a quiz | Mastery / readiness score (0–100 % or 0–1) is shown | | | |
| 8.2 | Score changes after a second quiz | Score updates (not stale cache) | | | |
| 8.3 | No previous quiz | Score is shown as 0 % or "not started"; no crash | | | |
| 8.4 | RTL check (AR only) | Score label and bar fill from right | | | |
| 8.5 | API call latency | Mastery endpoint responds in < 2 s on a stable connection | | | |

---

## 9. RTL and Arabic support — dedicated checks

| # | Check | Expected | ✓ | Bug |
|---|-------|----------|---|-----|
| 9.1 | App locale: Arabic | All system strings (back button, date pickers, alerts) are in Arabic | | |
| 9.2 | Text input fields | Cursor starts at the right edge; typing Arabic goes right-to-left | | |
| 9.3 | Numbers in Arabic locale | Displayed as Western digits (`0–9`), not Arabic-Indic | | |
| 9.4 | Mixed AR/EN text | Arabic text is RTL, inline English words are LTR (bidirectional) | | |
| 9.5 | Swipe direction | In AR mode, forward navigation swipes left-to-right (RTL convention) | | |
| 9.6 | Icon mirroring | Navigation arrows and directional icons are mirrored in AR | | |
| 9.7 | Scrollbar position | Scrollbar appears on the left side in AR mode | | |

---

## 10. Regression / edge cases

| # | Step | Expected | AR ✓ | EN ✓ | Bug |
|---|------|----------|------|------|-----|
| 10.1 | No internet connection | Meaningful offline message shown; no crash | | | |
| 10.2 | Session expires (token timeout) | User is redirected to login; no data loss | | | |
| 10.3 | Very slow connection (throttle to 2G) | Spinners shown; no silent failure | | | |
| 10.4 | Rotate device mid-flow | UI redraws correctly; no data lost | | | |
| 10.5 | Back button during upload | Upload is cancelled or continues in background (not both silently) | | | |

---

## Summary

| Flow | AR result | EN result | Blocker bugs | Notes |
|------|-----------|-----------|-------------|-------|
| 0. Smoke | | | | |
| 1. Sign up | | | | |
| 2. Log in | | | | |
| 3. Course list | | | | |
| 4. Upload PDF | | | | |
| 5. Upload audio | | | | |
| 6. Topic chunks | | | | |
| 7. Quiz attempt | | | | |
| 8. Mastery | | | | |
| 9. RTL/AR checks | — | — | | |
| 10. Edge cases | | | | |

**Overall result:** ☐ Pass &emsp; ☐ Fail (blocker found) &emsp; ☐ Partial (non-blocker bugs only)

---

> [!NOTE]
> **Dependencies not yet met (as of 2026-11-19):**
> - W2-05 (staging environment) is owned by Omar Negm — blocked until merged to `dev`.
> - W2-23 (Flutter auth + screens build) is owned by Omar Mustafa — blocked until distributed.
> - Until both are ready, checklist sections 1–8 cannot be run on a real staging build.
> - Sections 9 and 10 (RTL checks, edge cases) can be verified in the emulator once the
>   W2-22 Flutter project CI is green.
