---
name: test-report
description: Use when asked to test features or a branch and report results — web, backend, or mobile. Writes 2 positive + 1 negative test per feature in the project's own framework, actually runs them, and writes a Markdown pass/fail report.
---

# Test Report

For each feature under test: write **2 positive tests and 1 negative test**, run them for real,
and write a report from the actual results. Never report a result you didn't observe.

## 1. Scope

Test what the user names. If they name nothing, test what changed on the current branch:

```
git diff --name-only $(git merge-base HEAD origin/main 2>/dev/null || git merge-base HEAD main)...HEAD
```

Group the changed files into **features** (a user-visible behavior: "login", "create order",
"profile screen"), not files. State the feature list in one line before writing tests.

## 2. Detect stack and framework

Use what the project already has. Look at manifests and existing tests:

| Type | Signals | Use (in order of preference) |
|------|---------|------------------------------|
| Web | `playwright.config.*`, `cypress.config.*`, React/Vue/Angular/Next in `package.json` | Playwright → Cypress → existing |
| Backend (Node) | `express`/`fastify`/`nest` in `package.json` | existing Jest/Vitest/Mocha + supertest |
| Backend (Python) | `pyproject.toml`, `requirements.txt`, Django/FastAPI/Flask | pytest (+ Django test client / `TestClient`) |
| Backend (other) | `go.mod`, `Cargo.toml`, `pom.xml` | `go test`, `cargo test`, JUnit |
| Mobile (Flutter) | `pubspec.yaml` | `flutter test` (widget) / `integration_test` |
| Mobile (React Native) | `react-native` in `package.json` | Jest + RN Testing Library; Detox if configured |
| Mobile (native) | `*.xcodeproj`, `build.gradle` | XCTest / Espresso |

A project can be several types (e.g. web frontend + API) — test each feature at the layer it lives in.

**No test framework installed?** Stop and ask before installing the default from the table.
Don't add a dependency silently.

Match existing test conventions: folder, file naming, fixtures, helpers, base URL / test DB setup.
Read one or two existing tests first.

## 3. Write 3 tests per feature

| | Positive 1 | Positive 2 | Negative |
|-|-----------|-----------|----------|
| Meaning | The main happy path | A second valid path: different valid input, edge-of-valid value, or alternate route | Invalid input or bad state is **rejected cleanly** |
| Web | Fill form with valid data → submit → success state visible | Same flow, other valid variant (optional fields, boundary length, keyboard submit) | Invalid/empty input → error message shown, no navigation, nothing saved |
| Backend | Valid request → 2xx, correct body, side effect persisted | Other valid input (boundary, optional params, pagination) → correct result | Bad payload / missing auth / unknown id → correct 4xx, error body, **no** side effect |
| Mobile | Tap through main flow → expected screen/state | Alternate valid path (other input, back-and-retry) | Invalid input / offline / permission denied → error UI, app doesn't crash |

Rules:
- Name tests so the report is readable: `test_<feature>_positive_<what>`, `test_<feature>_negative_<what>`
  (or `it("<feature>: positive — …")` in JS).
- Assert on outcomes the user would notice (status, body, visible text, DB row), not internals.
- The negative test must assert **both** the rejection and the absence of the side effect.
- Each test independent: own data, no ordering dependency.
- Put tests in the project's test folders. They stay in the repo for re-running.

## 4. Run

Run only the new tests, with the project's own command (`npx playwright test <files>`,
`pytest <files> -v`, `flutter test <files>`, …). Start servers/emulators the way the
project documents (`webServer` in Playwright config, `docker compose up`, etc.).

- A test that fails: re-run it **once**. Passes on retry → mark it **flaky**, not passed.
- A test that can't run (no emulator, no DB, missing env var): mark **blocked** with the reason.
  Don't fake it, don't skip it silently.
- Failure from an app bug: **report it, don't fix app code.** Fixing is a separate request.
- Failure from a mistake in your test: fix the test and re-run; note it in the report.
- **Video (web and mobile):** record each test and keep the clip only when it fails, on this
  machine only — gitignore `test-reports/videos/` first and never commit a recording.
  Per-framework switches and safeguards: `references/video.md`.

## 5. Report

Write `test-reports/YYYY-MM-DD-<feature-or-branch>.md` in the tested project:

```markdown
# Test report — <feature or branch> — YYYY-MM-DD

**7/9 passed** · 1 failed · 1 blocked · web + backend · Playwright, pytest

| Feature | Type | Test | Result | Time | Video |
|---------|------|------|--------|------|-------|
| login | positive | valid credentials redirect to dashboard | ✅ pass | 1.2s | — |
| login | positive | remember-me keeps session | ✅ pass | 1.4s | — |
| login | negative | wrong password shows error, no session | ❌ fail | 0.9s | [clip](videos/2026-01-01/login-negative-wrong-password.webm) (local only) |

## Failures

### login — negative — wrong password shows error, no session
- **Error:** `expected "Invalid credentials" to be visible, got timeout`
- **Where:** `tests/e2e/login.spec.ts:42`
- **Likely cause:** app bug — error toast never renders on 401 (see `src/auth/Login.tsx:88`)
- **Video:** [clip](videos/2026-01-01/login-negative-wrong-password.webm) (local only)

## Blocked
- profile — mobile — all 3: no Android emulator available

## Re-run
`npx playwright test tests/e2e/login.spec.ts && pytest tests/api/test_orders.py -v`
```

Result values: ✅ pass, ❌ fail, ⚠️ flaky, ⛔ blocked. Every failure gets error, file:line,
a one-line cause guess labeled **app bug** or **test issue**, and its video link — or
`recording unavailable: <reason>` when there's no clip.

Finish by telling the user the summary line and the report path.
