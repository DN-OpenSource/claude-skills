#!/usr/bin/env node
// Plain browser tool for the benchmark baseline: Claude drives every move itself.
//   node browser_cli.mjs snapshot | click <id> | type <id> <text>     (attaches to $CDP)
import { createRequire } from "node:module";
const pw = createRequire(import.meta.url)("playwright-core");
const [cmd, id, ...rest] = process.argv.slice(2);
const b = await pw.chromium.connectOverCDP(process.env.CDP);
const page = b.contexts()[0].pages()[0];
const SNAP = () => { const sel="a,button,input,select,textarea,summary,[role=button],[role=link],[role=menuitem],[role=checkbox]"; const els={}; let i=0; document.querySelectorAll("[data-jev]").forEach(e=>e.removeAttribute("data-jev"));
  for (const el of document.querySelectorAll(sel)) { const r=el.getBoundingClientRect(), st=getComputedStyle(el);
    if (!r.width||!r.height||st.visibility==="hidden"||st.display==="none") continue; const id="e"+i++; el.setAttribute("data-jev",id);
    const tag=el.tagName.toLowerCase(); const role=el.getAttribute("role")||(tag==="a"?"link":tag==="input"?"textbox":tag);
    const label=el.getAttribute("aria-label")||(el.labels&&el.labels[0]&&el.labels[0].innerText)||el.placeholder||el.innerText||el.value||"";
    const box=el.closest("nav,header,footer,aside,form,dialog,[role=dialog],[role=menu],main,section");
    els[id]=`${role} '${label.trim().replace(/\s+/g," ").slice(0,80)}'${box?` (in ${box.getAttribute("aria-label")||box.tagName.toLowerCase()})`:""}`; }
  return { url: location.href, elements: els, text: document.body.innerText.replace(/\n\s*\n/g,"\n").slice(0,2500) }; };
try {
  if (cmd === "click") await page.click(`[data-jev="${id}"]`, { timeout: 3000 });
  else if (cmd === "type") await page.fill(`[data-jev="${id}"]`, rest.join(" "), { timeout: 3000 });
  if (cmd !== "snapshot") { try { await page.waitForLoadState("networkidle",{timeout:1500}) } catch {} await page.waitForTimeout(120); }
  console.log(JSON.stringify(await page.evaluate(SNAP)));
} catch (e) { console.log("ERROR: " + String(e.message).split("\n")[0]); }
await b.close().catch(()=>{});
