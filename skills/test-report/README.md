# test-report

Test the features you name (or whatever changed on the current branch) and get a pass/fail report built from real test runs.

## What this does

For every feature, the skill writes **3 tests** in the project's own test framework:

- **2 positive** — the main happy path, plus a second valid path (other input, boundary value, alternate route)
- **1 negative** — invalid input or bad state is rejected cleanly, and nothing is saved

It then **runs them for real**, retries failures once to catch flakiness, and writes `test-reports/YYYY-MM-DD-<feature-or-branch>.md`: a summary line, a per-test results table, error + file:line + likely cause for each failure, and the exact command to re-run.

## Video of failures

Web and mobile tests are recorded, and the clip is kept only when a test fails (Playwright, Cypress, Android, iOS simulator, Detox). Clips stay on your machine: `test-reports/videos/` is added to `.gitignore` first, nothing is ever committed, and every link in the report says **local only**. Details: [references/video.md](references/video.md).

## Works for

| Type | Frameworks |
|------|-----------|
| Web | Playwright, Cypress |
| Backend | pytest, Jest/Vitest + supertest, `go test`, `cargo test`, JUnit |
| Mobile | `flutter test` / `integration_test`, Jest + RN Testing Library, Detox, XCTest, Espresso |

It uses whatever the project already has. If no framework is set up, it asks before installing one.

## What it won't do

- Fix app code when a test exposes a bug — it reports the bug; fixing is a separate step.
- Report a result it didn't observe — tests that can't run (no emulator, no DB) are marked **blocked** with the reason.

## Details

See [SKILL.md](SKILL.md) for the stack-detection table, the positive/negative patterns per type, run rules, and the report template.
