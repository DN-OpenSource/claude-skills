#!/usr/bin/env python3
"""Browser-testing benchmark: Claude Code driving Chrome itself vs. handing the steps to the Jev runner.

Serves app.html (cookie banner, look-alike buttons, label mismatch, spinner, hidden account menu) on
localhost, starts headless Chrome per run, and checks success from the app's real state afterwards.

  cd scripts/bench_browser && npm i playwright-core && python3 bench_browser.py 2
Needs Chrome, Node, `claude` and a configured decision-maker provider. Spends real Claude/Jev credit.
"""
import functools, http.server, json, os, subprocess, sys, tempfile, threading, time, shutil
from pathlib import Path
SP = Path(__file__).resolve().parent
RUNNER = str(SP.parent / "browser_steps.mjs")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
URL = "http://127.0.0.1:8765/app.html"
STEPS = ["Open the sign-in page", "Fill the work email with dana@acme.io", "Fill the password with hunter22",
         "Submit the login form", "Open account settings", "Verify the page shows the email dana@acme.io"]
CLI = f"node {SP}/browser_cli.mjs"
TASK = "Test this web app, which is already open in a browser. Steps:\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(STEPS))
PROMPTS = {
 "claude": TASK + f"\n\nDrive the browser with `{CLI} snapshot`, `{CLI} click <id>` and `{CLI} type <id> <text>` "
           "(each prints the page's elements with ids, and its text, after acting). "
           "When done, report PASS or FAIL for each step, one line each.",
 "jev": TASK + f"\n\nRun all the steps at once with `node {RUNNER} --cdp $CDP --steps " +
        " ".join(json.dumps(s) for s in STEPS) + "` (it executes them with Jev; if it stops with exit 3 and a page "
        f"summary, do the remaining steps yourself with `{CLI} snapshot|click <id>|type <id> <text>`). "
        "When done, report PASS or FAIL for each step, one line each.",
}

def chrome(port):
    d = tempfile.mkdtemp()
    p = subprocess.Popen([CHROME, "--headless=new", f"--remote-debugging-port={port}", f"--user-data-dir={d}",
                          "--no-first-run", "--no-default-browser-check", URL], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2.0)
    return p, d

def state(cdp):
    js = ("const pw=require('playwright-core');(async()=>{const b=await pw.chromium.connectOverCDP(process.env.CDP);"
          "const p=b.contexts()[0].pages()[0];console.log(JSON.stringify(await p.evaluate(()=>({h:location.hash,"
          "e:window.__state&&window.__state.loginEmail}))));await b.close()})()")
    out = subprocess.run(["node", "-e", js], env={**os.environ, "CDP": cdp, "NODE_PATH": os.environ.get("NODE_PATH", str(SP / "node_modules"))},
                         capture_output=True, text=True).stdout
    d = json.loads(out or "{}")
    return d.get("h") == "#account" and d.get("e") == "dana@acme.io"

def run(mode, port=9333):
    proc, d = chrome(port)
    cdp = f"http://127.0.0.1:{port}"
    env = {**os.environ, "CDP": cdp, "NODE_PATH": os.environ.get("NODE_PATH", str(SP / "node_modules"))}
    t0 = time.monotonic()
    if mode == "runner":
        r = subprocess.run(["node", RUNNER, "--cdp", cdp, "--steps", *STEPS], env=env, capture_output=True, text=True)
        res = {"cost": 0, "turns": 0, "out": 0}
    else:
        r = subprocess.run(["claude", "-p", PROMPTS[mode], "--model", "sonnet", "--output-format", "json",
                            "--setting-sources", "project", "--no-session-persistence", "--max-budget-usd", "2",
                            "--allowedTools", "Bash"], env=env, capture_output=True, text=True, cwd=tempfile.mkdtemp(),
                           stdin=subprocess.DEVNULL)
        j = json.loads(r.stdout)
        u = j.get("usage", {})
        res = {"cost": j.get("total_cost_usd", 0), "turns": j.get("num_turns"), "out": u.get("output_tokens", 0),
               "in": u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0)}
    wall = time.monotonic() - t0
    ok = state(cdp)
    proc.kill(); shutil.rmtree(d, ignore_errors=True)
    return {"mode": mode, "wall_s": round(wall, 1), "success": ok, **res}

def serve():
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(SP))
    h.log_message = lambda *a: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 8765), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()


if __name__ == "__main__":
    serve()
    reps = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    rows = []
    for _ in range(reps):
        for mode in ("claude", "jev", "runner"):
            r = run(mode); rows.append(r); print(json.dumps(r), flush=True)
    print(f"\n{'mode':<8}{'wall s':>8}{'success':>9}{'Claude $':>10}{'turns':>7}{'ctx tokens':>12}{'out tok':>9}")
    for m in ("claude", "jev", "runner"):
        rs = [r for r in rows if r["mode"] == m]; avg = lambda k: sum(r.get(k) or 0 for r in rs) / len(rs)
        print(f"{m:<8}{avg('wall_s'):>8.1f}{sum(r['success'] for r in rs):>6}/{len(rs)}{avg('cost'):>10.3f}"
              f"{avg('turns'):>7.1f}{avg('in'):>12.0f}{avg('out'):>9.0f}")
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(json.dumps(rows, indent=2))
