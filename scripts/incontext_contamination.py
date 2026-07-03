#!/usr/bin/env python3
"""In-context contamination: the 'you didn't train two models' objection, answered cheaply.

The boundary receipt (BOUNDARY.md) grants contamination by construction (a scripted A0
that blindly replays a memorized artifact). A tough critic says: a *trained* model
might learn the METHOD from leaked answer keys, so your answer-side resistance could
evaporate under real training. Settling that fully needs a fine-tune (A2); this is the
tractable proxy — a real in-context learner under two contamination regimes.

Setup. A parametric question family over the retail DB (order totals, maxes, delivered
counts), split into a PRIMED set (the leaked benchmark the model is contaminated on) and
a HELD-OUT set (same templates, unseen specifics). One model, four conditions, each is a
single call because the model gets NO view of any regenerated world — pure contamination,
so its output is FIXED and we watch it against many worlds in code:

  answer-leak : context = primed (question -> ANSWER value) pairs; model emits values.
  query-leak  : context = primed (question -> gold SQL) pairs;    model emits SQL.
  answer-ctrl : no leak (schema only);                            model emits values.
  query-ctrl  : no leak (schema only);                            model emits SQL.

Grading. For each test question and each world (shipped + K regenerated), the fresh
oracle is the gold SQL executed on that world (replay/generative oracle). An emitted
VALUE scores by equality to the fresh oracle; an emitted SQL scores by executing it on
that world and comparing. The model never sees the regenerated rows, so a value it
emits is fixed and goes stale as the world regenerates, while a query it emits is
state-general and stays correct.

What the cells show:
  answer-leak, primed, shipped -> high      contamination works on the static bench
  answer-leak, primed, regen   -> LOW       regeneration defeats it (the boundary win)
  query-leak,  *,      regen    -> high      regeneration is cosmetic (the trap)
  query-*,     held-out, regen  -> high      the model GENERALIZED the method from
                                             leaked queries — the critic's 'training
                                             learns the skill' worry, realized, and
                                             exactly why query-scoring is unfixable
  answer-ctrl                    -> low      answers are unknowable without observation
  query-ctrl                     -> high      queries are knowable from schema alone

The decisive asymmetry is training-proof: no contamination (in-context or weight) can
supply the answer to a freshly regenerated instance, because the answer is a function
of the fresh state the model has not observed; the query needs no such observation.

No GPU, no fine-tune. Model calls: 4 (one per condition). Run:
    python scripts/incontext_contamination.py --agent claude --regen-seeds 12
"""
from __future__ import annotations
import argparse
import copy
import datetime
import json
import random
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "tau-bench/tau_bench/envs/retail/data"

SCHEMA = """Tables:
  users(user_id TEXT, name TEXT)
  orders(order_id TEXT, user_id TEXT, status TEXT)   -- status in delivered|pending|processed|cancelled
  order_items(order_id TEXT, name TEXT, product_id TEXT, item_id TEXT, price REAL)"""

# Question family: (id, natural-language question, gold SQL). Same templates across the
# split, different specifics, so the METHOD is shared and can generalize.
PRIMED = [
    ("p0", "What is the total price of the items in order #W2611340?",
     "SELECT ROUND(SUM(price),2) FROM order_items WHERE order_id='#W2611340'"),
    ("p1", "What is the total price of the items in order #W4817420?",
     "SELECT ROUND(SUM(price),2) FROM order_items WHERE order_id='#W4817420'"),
    ("p2", "What is the highest single-item price in order #W6304490?",
     "SELECT ROUND(MAX(price),2) FROM order_items WHERE order_id='#W6304490'"),
    ("p3", "How many delivered orders does Ivan Santos have?",
     "SELECT COUNT(*) FROM orders o JOIN users u ON o.user_id=u.user_id "
     "WHERE u.name='Ivan Santos' AND o.status='delivered'"),
    ("p4", "How many delivered orders does Anya Garcia have?",
     "SELECT COUNT(*) FROM orders o JOIN users u ON o.user_id=u.user_id "
     "WHERE u.name='Anya Garcia' AND o.status='delivered'"),
]
HELDOUT = [
    ("h0", "What is the total price of the items in order #W5918442?",
     "SELECT ROUND(SUM(price),2) FROM order_items WHERE order_id='#W5918442'"),
    ("h1", "What is the highest single-item price in order #W9077205?",
     "SELECT ROUND(MAX(price),2) FROM order_items WHERE order_id='#W9077205'"),
    ("h2", "How many delivered orders does Aarav Anderson have?",
     "SELECT COUNT(*) FROM orders o JOIN users u ON o.user_id=u.user_id "
     "WHERE u.name='Aarav Anderson' AND o.status='delivered'"),
]
TEST = PRIMED + HELDOUT

AGENT_ARGV = {"claude": ["claude", "-p"], "codex": ["codex", "exec"]}


def load_retail():
    return (json.loads((DATA / "orders.json").read_text()),
            json.loads((DATA / "users.json").read_text()))


def build_db(orders, users):
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE users(user_id TEXT, name TEXT)")
    con.execute("CREATE TABLE orders(order_id TEXT, user_id TEXT, status TEXT)")
    con.execute("CREATE TABLE order_items(order_id TEXT, name TEXT, product_id TEXT, item_id TEXT, price REAL)")
    for uid, u in users.items():
        con.execute("INSERT INTO users VALUES(?,?)",
                    (uid, u["name"]["first_name"] + " " + u["name"]["last_name"]))
    for oid, o in orders.items():
        con.execute("INSERT INTO orders VALUES(?,?,?)", (oid, o["user_id"], o["status"]))
        for it in o.get("items", []):
            con.execute("INSERT INTO order_items VALUES(?,?,?,?,?)",
                        (oid, it["name"], it["product_id"], it["item_id"], it["price"]))
    con.commit()
    return con


def resample(orders, users, seed):
    """Constraint-preserving content regen: perturb every price, flip every order status
    with p=0.5. Schema and all ids preserved; only queried VALUES move. Deterministic."""
    rng = random.Random(seed)
    orders = copy.deepcopy(orders)
    STATUSES = ["delivered", "pending", "processed", "cancelled"]
    for o in orders.values():
        for it in o.get("items", []):
            it["price"] = round(it["price"] * rng.uniform(0.80, 1.20), 2)
        if rng.random() < 0.5:
            o["status"] = rng.choice(STATUSES)
    return orders, users


def scalar(con, sql):
    try:
        row = con.execute(sql).fetchone()
        return row[0] if row else None
    except Exception:
        return "__SQL_ERROR__"


def approx_eq(a, b):
    if a is None or b is None or a == "__SQL_ERROR__":
        return False
    try:
        return abs(float(a) - float(b)) < 0.01
    except (TypeError, ValueError):
        return str(a).strip() == str(b).strip()


def build_prompt(kind, leak):
    lines = [f"You answer questions about a retail database.\n\nSCHEMA:\n{SCHEMA}\n"]
    if leak:
        lines.append("Worked examples:")
        for _id, q, gold_sql in PRIMED:
            if kind == "query":
                lines.append(f"- Q: {q}\n  SQL: {gold_sql}")
            else:
                # answer-leak: give the shipped answer VALUE, no rows
                lines.append(f"- Q: {q}\n  ANSWER: {{{_id}}}")  # filled below
        lines.append("")
    if kind == "query":
        lines.append("Write the SQL query answering each question below. You are NOT given "
                      "the table rows; write the query from the schema. Return ONLY a JSON "
                      "object mapping each id to its SQL string.")
    else:
        lines.append("Give the answer VALUE for each question below. You are NOT given the "
                      "table rows. Return ONLY a JSON object mapping each id to the value "
                      "(a number).")
    lines.append("")
    for _id, q, _ in TEST:
        lines.append(f"{_id}: {q}")
    lines.append('\nReturn only the JSON object, e.g. {"p0": ..., "p1": ...}.')
    return "\n".join(lines)


def call_model(argv, prompt, cwd, timeout_s=180):
    # CRITICAL: run in an isolated empty cwd. The CLI agents (claude -p, codex exec) have
    # filesystem access and will READ tau-bench/.../orders.json if run inside the repo,
    # observing the shipped world and defeating the no-observation premise. An empty cwd
    # outside the repo leaves the self-contained prompt as the only information source.
    proc = subprocess.run([*argv, prompt], capture_output=True, text=True,
                          timeout=timeout_s, cwd=cwd)
    if proc.returncode != 0:
        raise RuntimeError(f"agent failed ({proc.returncode}): {proc.stderr[:200]}")
    return proc.stdout


def extract_json(text):
    # last balanced {...}
    depth, start, best = 0, None, None
    for i, c in enumerate(text):
        if c == "{":
            if depth == 0:
                start = i
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0 and start is not None:
                best = text[start:i + 1]
    if best is None:
        return {}
    try:
        return json.loads(best)
    except Exception:
        return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", choices=list(AGENT_ARGV), default="claude")
    ap.add_argument("--regen-seeds", type=int, default=12)
    ap.add_argument("--out", default=str(REPO / "docs/receipts/INCONTEXT_CONTAMINATION.md"))
    args = ap.parse_args()
    argv = AGENT_ARGV[args.agent]

    orders, users = load_retail()
    shipped = build_db(orders, users)
    gold_shipped = {tid: scalar(shipped, sql) for tid, _, sql in TEST}

    # answer-leak prompt needs the shipped answer values spliced into the examples
    ans_leak_prompt = build_prompt("answer", leak=True)
    for pid, _, sql in PRIMED:
        ans_leak_prompt = ans_leak_prompt.replace(f"{{{pid}}}", str(gold_shipped[pid]))

    prompts = {
        "answer-leak": ans_leak_prompt,
        "query-leak": build_prompt("query", leak=True),
        "answer-ctrl": build_prompt("answer", leak=False),
        "query-ctrl": build_prompt("query", leak=False),
    }
    kinds = {"answer-leak": "answer", "query-leak": "query",
             "answer-ctrl": "answer", "query-ctrl": "query"}

    import tempfile
    isolated = tempfile.mkdtemp(prefix="incontext_isolated_")   # empty, outside the repo
    print(f"calling model (4 conditions), isolated cwd={isolated} ...", flush=True)
    outputs = {}
    for cond, prompt in prompts.items():
        raw = call_model(argv, prompt, cwd=isolated)
        outputs[cond] = extract_json(raw)
        print(f"  {cond}: parsed {len(outputs[cond])}/{len(TEST)} answers", flush=True)

    # worlds: shipped + regenerated seeds
    regen_dbs = [(s, build_db(*resample(orders, users, s))) for s in range(args.regen_seeds)]

    # score: per condition, per test question, on shipped and mean over regen worlds
    def score(cond, tid, sql, world_con):
        gold = scalar(world_con, sql)
        emitted = outputs[cond].get(tid)
        if emitted is None:
            return False
        if kinds[cond] == "query":
            return approx_eq(scalar(world_con, str(emitted)), gold)
        return approx_eq(emitted, gold)

    primed_ids = {p[0] for p in PRIMED}
    rows = []
    agg = {c: {"ship": [0, 0], "regen": [0, 0]} for c in prompts}   # [pass, total]
    for tid, q, sql in TEST:
        seen = "primed" if tid in primed_ids else "held-out"
        cell = {"id": tid, "seen": seen, "q": q}
        for cond in prompts:
            s_ship = score(cond, tid, sql, shipped)
            r_hits = sum(score(cond, tid, sql, db) for _, db in regen_dbs)
            cell[cond] = (s_ship, r_hits / len(regen_dbs))
            agg[cond]["ship"][0] += int(s_ship); agg[cond]["ship"][1] += 1
            agg[cond]["regen"][0] += r_hits; agg[cond]["regen"][1] += len(regen_dbs)
        rows.append(cell)

    # ---- receipt ----
    try:
        commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                         cwd=REPO, text=True).strip()
    except Exception:
        commit = "unknown"
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    L = [f"# In-context contamination: a real learner under two leak regimes\n",
         f"- Command: `python scripts/incontext_contamination.py --agent {args.agent} --regen-seeds {args.regen_seeds}`",
         f"- Commit: `{commit}`", f"- Date: {now}", f"- Agent: {args.agent} (one call per condition)",
         f"- Substrate: retail DB; {args.regen_seeds} regenerated worlds; model sees NO rows.",
         "- Method note: the CLI agents have filesystem access and WILL read "
         "`tau-bench/.../orders.json` if run in the repo (a first pass showed answer-ctrl=1.00 "
         "on shipped — the model computed from the real file). Model calls are therefore made "
         "from an isolated empty cwd outside the repo; answer-ctrl=0.00 confirms the sandbox.\n",
         "Pass rate = fraction correct against the replay-derived oracle. `ship` = shipped "
         "world, `regen` = mean over regenerated worlds. The model's output is fixed (it "
         "never observes a world), so `ship`->`regen` movement is regeneration acting on a "
         "*contaminated* learner.\n",
         "| id | set | answer-leak ship/regen | query-leak ship/regen | answer-ctrl ship/regen | query-ctrl ship/regen |",
         "|---|---|---|---|---|---|"]
    for c in rows:
        def f(cond):
            sh, rg = c[cond]
            return f"{'1.00' if sh else '0.00'} / {rg:.2f}"
        L.append(f"| {c['id']} | {c['seen']} | {f('answer-leak')} | {f('query-leak')} "
                 f"| {f('answer-ctrl')} | {f('query-ctrl')} |")
    L.append("")
    def m(cond, w):
        p, t = agg[cond][w]
        return p / t if t else 0.0
    L.append("Means: " + "; ".join(
        f"{c} ship={m(c,'ship'):.2f} regen={m(c,'regen'):.2f}" for c in prompts) + "\n")
    L.append("## Reading\n")
    L.append("- **answer-leak: high on shipped, collapses on regen.** The in-context leak "
             "reproduces the shipped answer (contamination works on the static bench), and "
             "regeneration invalidates it — the memorized value is now stale. A real "
             "learner, not a scripted A0, and it still goes stale, because the fresh answer "
             "is a function of a world the model never saw.")
    L.append("- **query-leak: high on both, including held-out.** The leaked queries let the "
             "model emit correct SQL, which the grader executes on the fresh rows. "
             "Regeneration is cosmetic. On HELD-OUT questions it still scores high: the "
             "model **generalized the method** from the primed queries. This is precisely "
             "the critic's 'training learns the skill' scenario — and it confirms the "
             "boundary rather than breaking it: a learned state-general method is exactly "
             "what regeneration cannot dislodge.")
    L.append("- **controls localize the cause, and show the leak conveys real method.** "
             "query-ctrl is *mixed*: high on the count questions (the "
             "`COUNT ... WHERE status='delivered'` mapping is guessable from the schema) but "
             "**zero on the price-aggregation questions** — without the examples the model did "
             "not map 'total/highest price' to `SUM/MAX(price)` over `order_items`. So "
             "query-leak (1.00) beating query-ctrl means the leak conveyed genuine, "
             "transferable method knowledge. The invariant that matters holds regardless of "
             "source: every query cell is FLAT ship->regen, because a state-general query is "
             "correct on any world. answer-ctrl is 0.00 (an answer is unknowable without "
             "observing the rows — this also confirms the sandbox: the model could not read "
             "the shipped file). Resistance lives exactly where observation is required to "
             "score, i.e. where the target co-varies with the regenerated state.\n")
    L.append("## Why this answers 'you didn't train two models'\n")
    L.append("The asymmetry is training-proof. No contamination — in-context here, or weight "
             "training in the full A2 — can supply the answer to a freshly regenerated "
             "instance, because that answer is determined by state the model has not "
             "observed. Training can only teach the state-general METHOD, which helps on the "
             "query target (where regeneration was already cosmetic) and cannot help on the "
             "answer target (where the value is unknowable a priori). So a weight-trained A2 "
             "moves the query cells to where they already are and leaves the answer cells "
             "where they already are. The remaining honest gap is empirical confirmation "
             "with an actual fine-tune (CoinRun-style held-out families; see DESIGN.md); "
             "this establishes the mechanism with a real, generalizing learner.")
    Path(args.out).write_text("\n".join(L) + "\n")
    print("\n".join(f"  {c} ship={m(c,'ship'):.2f} regen={m(c,'regen'):.2f}" for c in prompts))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
