# Video of failing tests

Web and mobile tests record video, and a recording is **kept only when the test fails** (on
the retry, so a flaky first run isn't saved as a failure). Passing tests already have a ✅;
their footage adds run time and disk and nothing a reviewer reads. Backend tests have no
screen: their Video cell is `—`.

Recordings can show typed passwords, tokens and personal data, and Playwright traces also
hold network calls, cookies and storage. So they stay **on this machine**.

## Before the first recording

1. Add `test-reports/videos/` (and the trace folder, if any) to the tested project's
   `.gitignore`, and tell the user you did it, in one line.
2. Run `git ls-files test-reports/videos` (and the trace folder). If anything is already
   tracked, tell the user. Don't remove it or rewrite history yourself.
3. Never commit, force-add, upload or embed a recording or trace, in any mode.

Save each kept clip as `test-reports/videos/YYYY-MM-DD/<feature>-<positive|negative>-<what>.<ext>`.

## By framework

| Framework | How to record failures only |
|-----------|------------------------------|
| Playwright | `use: { video: 'retain-on-failure', trace: 'retain-on-failure' }` and `outputDir: 'test-reports/videos/YYYY-MM-DD'` in the config, or pass `--video retain-on-failure` per run if the project's config shouldn't change. Open a trace with `npx playwright show-trace <zip>`. |
| Cypress | `video: true`, `videosFolder: 'test-reports/videos/YYYY-MM-DD'`, and in `setupNodeEvents` an `after:spec` handler that deletes the spec's video when it had no failures (Cypress's documented recipe). |
| Android (any framework) | Wrap each test: `adb shell screenrecord --time-limit 180 /sdcard/t.mp4 &`, run the test, stop the recorder, then `adb pull /sdcard/t.mp4 <clip>` only if the test failed; `adb shell rm /sdcard/t.mp4` either way. `screenrecord` stops at 180 s, so record **per test**, never per suite. |
| iOS simulator | `xcrun simctl io booted recordVideo --codec=h264 <clip>` in the background, run the test, stop it with Ctrl-C (SIGINT) so the file is finalized; delete it if the test passed. Needs macOS: mark it **unverified** when you can't run it. |
| Flutter / React Native / Detox | They run on the devices above: use the Android or iOS recorder around each test. Detox can also keep failures itself: `--record-videos failing`. |

## In the report

Add a **Video** column to the results table:

- failed test with a clip → `[clip](videos/YYYY-MM-DD/<file>) (local only)`
- failed test, no clip → `recording unavailable: <reason>` (headless backend, no emulator, iOS on Windows, recorder failed)
- passed, flaky or backend → `—`

Link only to files that exist. Every link says **local only**, because the clip isn't in git
and won't open on anyone else's machine.
