#!/usr/bin/env python3
"""Benchmark Claude Code with and without the decision-maker skill (real `claude -p` runs).

Builds a throwaway sandbox repo with known ground truth, runs the same task in
two modes, and compares Claude's token usage, cost, wall time and accuracy:

  baseline  plain Claude Code (no decision-maker plugin)
  jev       --plugin-dir decision-maker, prompt says "use the decision-maker skill"
  prefetch  --plugin-dir decision-maker with the prefetch hook on and NO hint in the prompt: the hook
            recognises the find task and scans the repo with Jev before Claude's first turn

Tasks
  hits   classify 80 grep hits for `orders`: real table access vs. noise
  files  find which of 100 source files implement refund logic (varied vocabulary,
         so a plain grep for "refund" gives both misses and false hits)
  files300  the same with 300 files

Run: python3 bench_claude_code.py --reps 2 [--model sonnet] [--tasks hits,files]
Spends real Claude and provider credit. Prints a table; --json saves raw results.
"""
import argparse
import json
import os
import random
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------- fixtures

REAL_HITS = [
    "app/repo/orders.py:{n}:    rows = db.execute('SELECT id, total FROM orders WHERE user_id = %s', (uid,))",
    "app/repo/orders.py:{n}:    db.execute('UPDATE orders SET status = %s WHERE id = %s', (status, oid))",
    "app/models.py:{n}:    __tablename__ = 'orders'",
    "app/services/checkout.py:{n}:    order = session.query(Order).filter(Order.id == order_id).one()",
    "app/jobs/cleanup.py:{n}:    cur.execute(\"DELETE FROM orders WHERE created_at < now() - interval '2 years'\")",
    "migrations/0012_orders.sql:{n}:ALTER TABLE orders ADD COLUMN discount_code text;",
    "app/api/admin.py:{n}:    q = Order.objects.filter(status='pending').order_by('-created_at')",
    "app/reports/sales.py:{n}:    df = pd.read_sql('SELECT sum(total) FROM orders GROUP BY day', conn)",
    "app/repo/orders.py:{n}:    session.add(Order(user_id=uid, total=total))",
    "app/services/refunds.py:{n}:    db.execute('INSERT INTO orders_audit SELECT * FROM orders WHERE id = %s', (oid,))",
]
NOISE_HITS = [
    "docs/changelog.md:{n}: - Fixed sort orders in the admin list",
    "app/ui/table.tsx:{n}:  // keep column orders stable when resizing",
    "README.md:{n}: Follow the orders of operations below to deploy.",
    "app/styles/grid.css:{n}:  /* flex orders for mobile */",
    "app/i18n/en.json:{n}:  \"no_orders_yet\": \"You have no orders yet. Start shopping!\",",
    "app/military/ranks.py:{n}:    # standing orders for the simulation units",
    "tests/fixtures/README.md:{n}: Fixtures load in alphabetical orders.",
    "app/api/docs.py:{n}:    \"\"\"Returns the user's orders page HTML template name.\"\"\"",
    "scripts/sort.py:{n}:# merge sort that preserves input orders for equal keys",
    "app/emails/templates.py:{n}:    subject = 'Your recent orders are on the way'",
]

REFUND_FILES = {
    "src/billing/refunds.py": "def issue_refund(payment_id, amount):\n    gateway.refund(payment_id, amount)\n    ledger.record('refund', payment_id, -amount)\n",
    "src/billing/credit_notes.py": "def issue_credit_note(invoice, lines):\n    note = CreditNote(invoice=invoice, total=-sum(l.amount for l in lines))\n    note.post_to_ledger()\n    return note\n",
    "src/payments/reversal.py": "def reverse_payment(charge):\n    if charge.captured:\n        return stripe.Refund.create(charge=charge.id)\n    return stripe.Charge.cancel(charge.id)\n",
    "src/orders/returns.py": "def complete_return(rma):\n    restock(rma.items)\n    return_funds(rma.order.payment, rma.amount_due_back)\n",
    "src/api/refund_routes.py": "@router.post('/orders/{oid}/refund')\ndef refund_order(oid: int, body: RefundIn):\n    return billing.issue_refund(body.payment_id, body.amount)\n",
    "src/billing/proration.py": "def prorated_credit(subscription, cancel_date):\n    unused = subscription.days_left(cancel_date)\n    amount = subscription.daily_rate * unused\n    wallet.add_credit(subscription.customer, amount)  # give back unused time\n",
    "src/workers/refund_retry.py": "def retry_failed_refunds():\n    for r in Refund.objects.filter(status='failed'):\n        gateway.refund(r.payment_id, r.amount)\n",
    "src/payments/wallet.py": "def return_to_wallet(order):\n    # customer cancelled before shipping: put the full charge back in their balance\n    wallet.add_credit(order.customer, order.total)\n",
    "src/billing/adjustments.py": "def apply_goodwill_adjustment(account, amount):\n    ledger.record('payout_to_customer', account.id, -amount)\n    gateway.transfer_to_card(account.card, amount)\n",
}
DISTRACTOR_FILES = {
    # money returns to the MERCHANT, not the customer (an earlier version mislabelled this as a refund)
    "src/payments/chargeback.py": "def handle_chargeback_won(dispute):\n    # money comes back to the merchant: undo the provisional debit\n    ledger.credit(dispute.merchant, dispute.amount)\n",
    "src/ui/pricing_copy.py": "PLAN_NOTE = 'Annual plans are non-refundable after 30 days.'\n",
    "src/i18n/en.py": "STRINGS = {'refund_policy_title': 'Refund policy', 'refund_policy_body': 'See our terms.'}\n",
    "src/legal/terms.py": "TERMS = '''Section 7. Refunds are at our sole discretion.'''\n",
    "src/analytics/events.py": "EVENT_NAMES = ['page_view', 'signup', 'refund_page_viewed', 'checkout_started']\n",
    "src/billing/invoices.py": "def create_invoice(order):\n    return Invoice(order=order, total=order.total)\n",
    "src/payments/charge.py": "def charge(card, amount):\n    return stripe.Charge.create(source=card, amount=amount)\n",
}
FILLER_TOPICS = ["users", "auth", "email", "search", "cache", "reports", "inventory", "shipping", "notifications",
                 "settings", "uploads", "audit", "feature_flags", "sessions", "themes", "webhooks_in", "exports"]


def filler(topic, i, rng):
    funcs = []
    for j in range(rng.randint(4, 8)):
        funcs.append(f"def {topic}_op_{i}_{j}(ctx, item):\n"
                     f"    \"\"\"Handle {topic} step {j} for the {topic} module.\"\"\"\n"
                     f"    value = ctx.get('{topic}_{j}', {rng.randint(1, 99)})\n"
                     f"    if item is None:\n        return value\n"
                     f"    return [x * value for x in item if x]\n")
    return f"import logging\nlog = logging.getLogger(__name__)\n\n" + "\n\n".join(funcs)


def build_sandbox(root: Path, seed=7, n_files=100):
    rng = random.Random(seed)
    # hits task: 40 real / 40 noise, shuffled
    hits = [(h.format(n=rng.randint(5, 400)), True) for h in REAL_HITS * 4] + \
           [(h.format(n=rng.randint(5, 400)), False) for h in NOISE_HITS * 4]
    rng.shuffle(hits)
    (root / "hits.txt").write_text("\n".join(h for h, _ in hits) + "\n")
    truth_hits = {i + 1 for i, (_, real) in enumerate(hits) if real}
    # files task
    files = dict(REFUND_FILES)
    files.update(DISTRACTOR_FILES)
    for i in range(n_files - len(files)):
        topic = FILLER_TOPICS[i % len(FILLER_TOPICS)]
        files[f"src/{topic}/mod_{i}.py"] = filler(topic, i, rng)
    for path, body in files.items():
        f = root / path
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(body)
    subprocess.run(["git", "init", "-q"], cwd=root)
    return {"hits": truth_hits, "files": set(REFUND_FILES)}


TASKS = {
    "hits": ("hits.txt contains grep hits for the word 'orders' (format path:line: text), one per line. "
             "Which hits.txt lines are real code that uses the `orders` database table (SQL queries, ORM models or "
             "table mappings, migrations), as opposed to the word 'orders' in comments, docs, UI text or CSS? "
             "Answer with ONLY the hits.txt line numbers, comma-separated, nothing else."),
    "files300": None,
    "files": ("Which files under src/ implement or call logic that sends money back to a customer "
              "(refunds, credit notes, payment reversals, returning funds or credit)? Ignore files that only "
              "mention refunds in text, copy or analytics. Answer with ONLY the file paths, one per line, nothing else."),
}
JEV_HINT = " Use the decision-maker skill for the classification."
TASKS["files300"] = TASKS["files"]


def score(task, answer, truth):
    import re
    if task == "hits":
        got = {int(x) for x in re.findall(r"\b\d+\b", answer)}
    else:
        got = {m.strip().lstrip("./") for m in re.findall(r"src/[\w/]+\.py", answer)}
    tp = len(got & truth)
    precision = tp / len(got) if got else 0.0
    recall = tp / len(truth)
    return round(precision, 2), round(recall, 2)


def run(mode, task, model, budget):
    root = Path(tempfile.mkdtemp(prefix=f"dm-bench-{task}-"))
    truth = build_sandbox(root, n_files=300 if task == "files300" else 100)["files" if task == "files300" else task]
    cmd = ["claude", "-p", TASKS[task] + (JEV_HINT if mode == "jev" else ""), "--model", model,
           "--output-format", "json", "--setting-sources", "project", "--no-session-persistence",
           "--max-budget-usd", str(budget), "--allowedTools", "Bash", "Read", "Grep", "Glob", "Skill"]
    if mode in ("jev", "prefetch"):
        cmd += ["--plugin-dir", str(PLUGIN)]
    env = {**os.environ, "DECISION_MAKER_GUARD": "prefetch" if mode == "prefetch" else ""}
    t0 = time.monotonic()
    proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=900, env=env,
                          stdin=subprocess.DEVNULL)
    wall = time.monotonic() - t0
    shutil.rmtree(root, ignore_errors=True)
    d = json.loads(proc.stdout)
    u = d.get("usage", {})
    p, r = score(task, d.get("result", ""), truth)
    return {"mode": mode, "task": task, "cost": d.get("total_cost_usd", 0), "turns": d.get("num_turns"),
            "wall_s": round(wall, 1), "input": u.get("input_tokens", 0),
            "cache_write": u.get("cache_creation_input_tokens", 0), "cache_read": u.get("cache_read_input_tokens", 0),
            "output": u.get("output_tokens", 0), "precision": p, "recall": r, "error": d.get("is_error")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--tasks", default="hits,files")
    ap.add_argument("--budget", type=float, default=2.0, help="max USD per run")
    ap.add_argument("--modes", default="baseline,jev,prefetch")
    ap.add_argument("--json")
    args = ap.parse_args()
    rows = []
    for task in args.tasks.split(","):
        for rep in range(args.reps):
            for mode in args.modes.split(","):
                r = run(mode, task, args.model, args.budget)
                rows.append(r)
                print(json.dumps(r), flush=True)
    print(f"\n{'task':<6}{'mode':<10}{'cost $':>8}{'in+cache_w':>12}{'cache_r':>9}{'output':>8}{'turns':>6}"
          f"{'wall s':>8}{'prec':>6}{'recall':>7}")
    for task in args.tasks.split(","):
        for mode in args.modes.split(","):
            rs = [r for r in rows if r["task"] == task and r["mode"] == mode]
            avg = lambda k: sum(r[k] or 0 for r in rs) / len(rs)
            print(f"{task:<6}{mode:<10}{avg('cost'):>8.3f}{avg('input') + avg('cache_write'):>12.0f}"
                  f"{avg('cache_read'):>9.0f}{avg('output'):>8.0f}{avg('turns'):>6.1f}{avg('wall_s'):>8.1f}"
                  f"{avg('precision'):>6.2f}{avg('recall'):>7.2f}")
    if args.json:
        Path(args.json).write_text(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
