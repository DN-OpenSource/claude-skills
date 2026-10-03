#!/usr/bin/env node
// browser_steps.mjs: run plain-English test steps in a real browser, with Jev deciding each move.
//
// Per page view, ONE Jev call (speculative fan-out) asks together:
//   done     - is the step already done?           → next step
//   loading  - still loading?                      → wait, look again
//   blocked  - modal/cookie banner/overlay?        → dismiss it (one more Jev choice), look again
//   target   - which element performs the step?    → click / type when confident
// Anything Jev isn't confident about stops the run with exit 3 and prints the page summary,
// so the calling agent (Claude) takes over only for that step. Verify steps are one noul.
//
//   node browser_steps.mjs --url http://localhost:3000 --steps "Open the sign-in page" "Fill the email with a@b.co" ...
//   node browser_steps.mjs --cdp http://127.0.0.1:9222 --steps-file steps.txt      (attach to a running Chrome)
// Needs: Node 18+, `npm i playwright-core` (resolved from the cwd or NODE_PATH), and Chrome installed.
// Exit codes: 0 all passed · 1 a verify step failed · 2 setup error · 3 needs the agent (unsure step).
import { createRequire } from "node:module";
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const DECIDE = join(dirname(fileURLToPath(import.meta.url)), "decide.py");
const ACT = Number(process.env.DECISION_MAKER_ACT || 0.8);
// Picking the best element only needs the top option to clearly lead: a wrong, harmless click is
// caught by the next look (`done`). Clicks that can do damage still need ACT.
const CLICK_ACT = Number(process.env.DECISION_MAKER_CLICK_ACT || 0.6);
const RISKY = /\b(delete|remove|pay|purchase|buy|place order|confirm order|transfer|send|publish|deactivate|cancel subscription)\b/i;
const MAX_MOVES = 6;          // actions per step before giving up (menus can need 2-3 clicks)
const CLICK_TIMEOUT = 3000;

function args() {
  const a = process.argv.slice(2), o = { steps: [] };
  for (let i = 0; i < a.length; i++) {
    if (a[i] === "--url") o.url = a[++i];
    else if (a[i] === "--cdp") o.cdp = a[++i];
    else if (a[i] === "--steps-file") o.steps.push(...readFileSync(a[++i], "utf8").split("\n").map(s => s.trim()).filter(Boolean));
    else if (a[i] === "--headed") o.headed = true;
    else if (a[i] === "--steps") { while (a[i + 1] && !a[i + 1].startsWith("--")) o.steps.push(a[++i]); }
  }
  return o;
}

let jevCalls = 0, jevMs = 0;
function jev(state, questions) {
  const t = Date.now();
  jevCalls++;
  const out = execFileSync("python3", [DECIDE, "ask", "--questions", JSON.stringify(questions), "--retries", "2"],
                           { input: JSON.stringify(state), encoding: "utf8",
                             env: { ...process.env, DECISION_MAKER_SOURCE: "browser" } });
  jevMs += Date.now() - t;
  return JSON.parse(out).answers;
}

// Visible interactive elements, tagged so we can act on them by id.
const SNAPSHOT = () => {
  const sel = "a,button,input,select,textarea,summary,[role=button],[role=link],[role=menuitem],[role=checkbox],[role=tab],[role=option]";
  const els = {}; let i = 0;
  document.querySelectorAll("[data-jev]").forEach(e => e.removeAttribute("data-jev"));   // ids from older views
  for (const el of document.querySelectorAll(sel)) {
    const r = el.getBoundingClientRect(), st = getComputedStyle(el);
    if (!r.width || !r.height || st.visibility === "hidden" || st.display === "none" || el.disabled) continue;
    const id = "e" + i++;
    el.setAttribute("data-jev", id);
    const tag = el.tagName.toLowerCase();
    const role = el.getAttribute("role") || (tag === "a" ? "link" : tag === "input" ? `textbox${el.type && el.type !== "text" ? ":" + el.type : ""}` : tag);
    const label = el.getAttribute("aria-label") || (el.labels && el.labels[0] && el.labels[0].innerText) ||
                  el.placeholder || el.innerText || el.value || el.title || "";
    const box = el.closest("nav,header,footer,aside,form,dialog,[role=dialog],[role=menu],main,section");
    const where = box ? (box.getAttribute("aria-label") || box.tagName.toLowerCase()) : "";
    els[id] = `${role} '${label.trim().replace(/\s+/g, " ").slice(0, 80)}'${where ? ` (in ${where})` : ""}`;
  }
  return { url: location.href, elements: els, text: document.body.innerText.replace(/\n\s*\n/g, "\n").slice(0, 2500) };
};

const kind = s => /^(fill|type|enter|input)\b/i.test(s) ? "type" : /^(verify|check|assert|expect|confirm)\b/i.test(s) ? "verify" : "click";
const valueOf = s => (s.match(/\bwith\s+["']?(.+?)["']?\s*$/i) || [])[1];

// Reading the page right after a navigation can hit a context being torn down: retry briefly.
async function look(page) {
  for (let i = 0; ; i++) {
    try { return await page.evaluate(SNAPSHOT); }
    catch (e) { if (i >= 4) throw e; await page.waitForTimeout(250); }
  }
}

async function settle(page) {
  try { await page.waitForLoadState("networkidle", { timeout: 1500 }); } catch {}
  await page.waitForTimeout(120);
}

async function runStep(page, step) {
  const t0 = Date.now(), k = kind(step);
  if (k === "verify") {
    const snap = await look(page);
    const a = jev({ step, url: snap.url, page_text: snap.text },
                  { ok: { type: "noul", instructions: "Is `step` true on this page (judge from `page_text` and `url`)?" } }).ok;
    const conf = Math.max(a.noul, 1 - a.noul);
    return { step, result: conf < ACT ? "needs-agent" : a.noul >= 0.5 ? "passed" : "FAILED", p: a.noul, ms: Date.now() - t0, snap };
  }
  const moves = [];
  for (let n = 0; n < MAX_MOVES; n++) {
    const snap = await look(page);
    const opts = { ...snap.elements, none: "None of these elements helps with the step, not even by opening a menu or navigating to the right page" };
    const q = {
      target: { type: "choice", criteria: opts, instructions: k === "type"
        ? "Test step: `step`. Which input field should receive the value?"
        : "Test step: `step`. Which element should be clicked next to perform it? If the step needs a menu or panel opened first, pick the element that opens it." },
      blocked: { type: "noul", instructions: "Is the page covered by a modal, cookie banner, overlay or login wall that must be dismissed before using it?" },
      loading: { type: "noul", instructions: "Is the page still loading (spinner, skeleton, 'Loading…', 'Signing you in…')?" },
    };
    if (k === "click" && n > 0) q.done = { type: "noul", instructions: "Has `step` been accomplished, so the page now shows its result?" };
    const a = jev({ step, already_done: moves, url: snap.url, page_text: snap.text }, q);
    if (a.done && a.done.noul >= ACT) return { step, result: "passed", moves, ms: Date.now() - t0 };
    if (a.loading.noul >= 0.5) { await page.waitForTimeout(400); continue; }
    if (a.blocked.noul >= 0.5 && !/cookie|banner|consent|modal|dialog|popup/i.test(step)) {
      const d = jev({ url: snap.url, page_text: snap.text }, { dismiss: { type: "choice", criteria: opts,
        instructions: "Which element closes or accepts the overlay/banner/modal so the page underneath can be used?" } }).dismiss;
      if (d.confidence >= ACT && d.choice !== "none") {
        await page.click(`[data-jev="${d.choice}"]`, { timeout: CLICK_TIMEOUT });
        moves.push(`dismissed ${snap.elements[d.choice]}`);
        await settle(page);
        continue;
      }
    }
    const t = a.target;
    const need = k === "click" && !RISKY.test(snap.elements[t.choice] || "") ? CLICK_ACT : ACT;
    if (t.confidence < need || t.choice === "none")
      return { step, result: "needs-agent", moves, ms: Date.now() - t0,
               jev: { choice: t.choice, confidence: t.confidence, top: t.probabilities }, snap };
    const sel = `[data-jev="${t.choice}"]`;
    if (k === "type") {
      const v = valueOf(step);
      if (v === undefined) return { step, result: "needs-agent", reason: "no 'with <value>' in step", ms: Date.now() - t0, snap };
      await page.fill(sel, v, { timeout: CLICK_TIMEOUT });
      moves.push(`typed into ${snap.elements[t.choice]}`);
      return { step, result: "passed", moves, ms: Date.now() - t0 };
    }
    await page.click(sel, { timeout: CLICK_TIMEOUT });
    moves.push(`clicked ${snap.elements[t.choice]} (${t.confidence.toFixed(2)})`);
    await settle(page);
  }
  return { step, result: "needs-agent", reason: `not done after ${MAX_MOVES} moves`, moves, ms: Date.now() - t0 };
}

async function main() {
  const o = args();
  if (!o.steps.length || !(o.url || o.cdp)) {
    console.error("usage: browser_steps.mjs (--url URL | --cdp ENDPOINT [--url URL]) --steps 'step' ... | --steps-file F");
    process.exit(2);
  }
  let pw;
  try { pw = createRequire(join(process.cwd(), "x.js"))("playwright-core"); }
  catch { console.error("playwright-core not found: run `npm i playwright-core` here or set NODE_PATH"); process.exit(2); }
  const t0 = Date.now();
  const browser = o.cdp ? await pw.chromium.connectOverCDP(o.cdp)
                        : await pw.chromium.launch({ channel: "chrome", headless: !o.headed });
  const ctx = browser.contexts()[0] || await browser.newContext();
  const page = ctx.pages()[0] || await ctx.newPage();
  if (o.url) { await page.goto(o.url); await settle(page); }
  let code = 0;
  for (const step of o.steps) {
    let r;
    try { r = await runStep(page, step); }
    catch (e) { r = { step, result: "needs-agent", error: String(e.message || e).split("\n")[0] }; }
    const { snap, ...shown } = r;
    console.log(JSON.stringify(shown));
    if (r.result !== "passed") {
      code = r.result === "FAILED" ? 1 : 3;
      if (snap) console.log(JSON.stringify({ page_for_agent: { url: snap.url, elements: snap.elements, text: snap.text.slice(0, 1200) } }));
      break;
    }
  }
  console.log(JSON.stringify({ summary: code === 0 ? "all steps passed" : code === 1 ? "verify failed" : "stopped: needs agent",
                               total_ms: Date.now() - t0, jev_calls: jevCalls, jev_ms: jevMs }));
  if (!o.cdp) await browser.close(); else await browser.close().catch(() => {});
  process.exit(code);
}
main().catch(e => { console.error(e); process.exit(2); });
