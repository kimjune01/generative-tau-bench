#!/usr/bin/env python3
"""The cross-class boundary, for bench builders (DESIGN.md proof-ladder step 5).

The question a benchmark builder actually has is not "is regeneration good?" but
"if I regenerate my benchmark's state to fight contamination, will it work?" The
answer is a decision rule, and this script demonstrates it on ONE substrate (the
tau-bench retail DB) with ONE regeneration operator (a constraint-preserving content
resample), varying only *what is scored*. A model is "contaminated" here in the
strongest sense: it has memorized the shipped instance's answer artifact perfectly.
We measure whether that memorization still passes after regeneration.

Three regimes a builder could choose:

  1. STATIC ANSWER KEY (no regeneration). The leaked artifact is the graded answer.
     A contaminated model passes by definition. Resistance = 0. (Not run; it is 1.00
     by construction and is the baseline every static benchmark sits at.)

  2. REGENERATE + SCORE A STATE-INVARIANT ARTIFACT (the SQL *query*). This is
     text-to-SQL: the grader executes the submitted query against the regenerated
     rows. The correct query is a fixed point of regeneration, so a model that leaked
     the gold query STILL passes every regenerated instance. Regeneration bought
     nothing. This is the trap: contamination-resistance does not follow from
     regenerating state alone.

  3. REGENERATE + SCORE THE STATE-EQUIVARIANT TARGET, ORACLE DERIVED BY REPLAY (the
     tau-bench shape). The graded target is the answer VALUE, and the fresh oracle is
     computed by re-executing the reference against the regenerated state (here, the
     gold SQL; in tau-bench, the golden action program). A model that leaked the
     shipped answer fails exactly when regeneration moved the answer. Resistance =
     the fraction of instances where the scored target actually changed. The replay/
     generative oracle is what makes this regime free: no re-annotation per seed.

The double result (regime 2 vs 3 on the same DB, same resample) IS precondition 5:
resistance is a property of scored-target equivariance, not of the domain or of how
hard you regenerate. The generative oracle contributes to resistance only when it is
wired to a target that co-varies with the regenerated state.

No model calls. Deterministic given --seeds. Writes docs/receipts/BOUNDARY.md.

Run:  uv run python scripts/boundary_experiment.py --seeds 200
"""
from __future__ import annotations
import argparse
import copy
import datetime
import json
import random
import sqlite3
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "tau-bench/tau_bench/envs/retail/data"


def load_retail():
    orders = json.loads((DATA / "orders.json").read_text())
    users = json.loads((DATA / "users.json").read_text())
    return orders, users


def build_db(orders, users):
    """In-memory sqlite mirror of the slice the questions touch."""
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE users(user_id TEXT, name TEXT)")
    con.execute("CREATE TABLE orders(order_id TEXT, user_id TEXT, status TEXT)")
    con.execute("CREATE TABLE order_items(order_id TEXT, name TEXT, "
                "product_id TEXT, item_id TEXT, price REAL)")
    for uid, u in users.items():
        con.execute("INSERT INTO users VALUES(?,?)", (uid, u["name"]["first_name"] + " " + u["name"]["last_name"]))
    for oid, o in orders.items():
        con.execute("INSERT INTO orders VALUES(?,?,?)", (oid, o["user_id"], o["status"]))
        for it in o.get("items", []):
            con.execute("INSERT INTO order_items VALUES(?,?,?,?,?)",
                        (oid, it["name"], it["product_id"], it["item_id"], it["price"]))
    con.commit()
    return con


def resample(orders, users, seed, target_user):
    """Constraint-preserving content regeneration: perturb item prices and flip a
    subset of the target user's order statuses. Schema and every id are preserved
    (so the gold SQL stays well-formed); only the VALUES the questions ask about move.
    Deterministic in seed."""
    rng = random.Random(seed)
    orders = copy.deepcopy(orders)
    for o in orders.values():
        for it in o.get("items", []):
            factor = rng.uniform(0.80, 1.20)
            it["price"] = round(it["price"] * factor, 2)
    # flip statuses among the target user's orders (keeps them a valid status set)
    STATUSES = ["delivered", "pending", "processed", "cancelled"]
    for oid in users[target_user]["orders"]:
        if oid in orders and rng.random() < 0.5:
            orders[oid]["status"] = rng.choice(STATUSES)
    return orders, users


def scalar(con, sql):
    cur = con.execute(sql)
    row = cur.fetchone()
    return row[0] if row else None


# --- text-to-SQL instances: fixed NL question, fixed gold SQL, state-dependent answer
YUSUF = "Yusuf Rossi"
INSTANCES = [
    {
        "q": "What is the total price of the items in order #W2378156?",
        "gold_sql": "SELECT ROUND(SUM(price),2) FROM order_items WHERE order_id='#W2378156'",
    },
    {
        "q": f"How many delivered orders does {YUSUF} have?",
        "gold_sql": ("SELECT COUNT(*) FROM orders o JOIN users u ON o.user_id=u.user_id "
                     f"WHERE u.name='{YUSUF}' AND o.status='delivered'"),
    },
    {
        "q": "What is the highest single-item price in order #W2378156?",
        "gold_sql": "SELECT ROUND(MAX(price),2) FROM order_items WHERE order_id='#W2378156'",
    },
]


def run(seeds: int):
    orders, users = load_retail()
    # target user id for the count question
    target_user = next(uid for uid, u in users.items()
                       if u["name"]["first_name"] + " " + u["name"]["last_name"] == YUSUF)

    shipped_con = build_db(orders, users)
    shipped_ans = {i: scalar(shipped_con, inst["gold_sql"]) for i, inst in enumerate(INSTANCES)}

    # per instance: pass counts for the two regenerated regimes, and change rate
    q_pass = [0] * len(INSTANCES)      # regime 2: leaked SQL query re-executed
    a_pass = [0] * len(INSTANCES)      # regime 3: leaked answer value, replay oracle
    changed = [0] * len(INSTANCES)
    for s in range(seeds):
        r_orders, r_users = resample(orders, users, s, target_user)
        con = build_db(r_orders, r_users)
        for i, inst in enumerate(INSTANCES):
            gold = scalar(con, inst["gold_sql"])                 # fresh oracle by replay
            # regime 2: adversary submitted the leaked gold SQL; grader executes it now
            leaked_query_result = scalar(con, inst["gold_sql"])
            if leaked_query_result == gold:
                q_pass[i] += 1
            # regime 3: adversary submitted the leaked shipped answer value
            if shipped_ans[i] == gold:
                a_pass[i] += 1
            else:
                changed[i] += 1
        con.close()
    return shipped_ans, q_pass, a_pass, changed, seeds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=200)
    ap.add_argument("--out", default=str(REPO / "docs/receipts/BOUNDARY.md"))
    args = ap.parse_args()

    shipped_ans, q_pass, a_pass, changed, n = run(args.seeds)

    try:
        commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                         cwd=REPO, text=True).strip()
    except Exception:
        commit = "unknown"
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    L = []
    L.append("# The cross-class boundary: a decision rule for bench builders\n")
    L.append(f"- Command: `uv run python scripts/boundary_experiment.py --seeds {n}`")
    L.append(f"- Commit: `{commit}`")
    L.append(f"- Date: {now}")
    L.append(f"- Substrate: tau-bench retail DB in sqlite; one content resampler "
             f"(prices x U(0.8,1.2), status flips for the target user); {n} seeds.\n")
    L.append("A **contaminated** adversary has perfectly memorized the shipped instance's "
             "answer artifact. We measure whether that memorization still PASSES after "
             "the exact same regeneration, under two scored targets:\n")
    L.append("- **Regime 2 (state-invariant target = the SQL query):** the leaked artifact "
             "is the gold query; the grader executes it against the regenerated rows.")
    L.append("- **Regime 3 (state-equivariant target = the answer value, replay oracle):** "
             "the leaked artifact is the shipped answer; the fresh oracle re-executes the "
             "reference on the regenerated rows.\n")
    L.append("| # | Question | shipped answer | R2 leaked-query pass | R3 leaked-answer pass | answer moved |")
    L.append("|---|---|---|---|---|---|")
    for i, inst in enumerate(INSTANCES):
        L.append(f"| {i} | {inst['q']} | {shipped_ans[i]} | "
                 f"**{q_pass[i]/n:.3f}** | **{a_pass[i]/n:.3f}** | {changed[i]/n:.3f} |")
    L.append("")
    q_mean = sum(q_pass) / (n * len(INSTANCES))
    a_mean = sum(a_pass) / (n * len(INSTANCES))
    L.append(f"Means across {len(INSTANCES)} instances: leaked-query **{q_mean:.3f}**, "
             f"leaked-answer **{a_mean:.3f}**.\n")
    L.append("## Reading\n")
    L.append("- **Regime 2 is the trap.** Leaked-query pass is **1.000**: regenerating the "
             "rows did nothing, because the correct SQL query is a fixed point of "
             "regeneration. Any benchmark whose scored artifact is a state-general program "
             "(text-to-SQL, competitive coding, a policy) inherits this — regeneration "
             "hardens the grader against wrong answers but buys ZERO contamination "
             "resistance. This is the common and costly mistake.")
    L.append("  - *Isn't R2 circular?* No — that is the vulnerability, stated precisely. "
             "A query that instead smuggled the memorized answer as a literal "
             "(`SELECT 1819.92`) would collapse to regime 3 and BE caught (a constant is "
             "state-equivariant-scored the moment it is compared to the fresh answer). "
             "What survives regeneration is exactly the state-GENERAL program. So the "
             "boundary runs inside text-to-SQL too: regeneration catches answer-smuggling "
             "leaks and misses the realistic query leak.")
    L.append("- **Regime 3 is the recommendation.** Leaked-answer pass collapses toward "
             "`1 - (answer moved)`: resistance is exactly the rate at which regeneration "
             "moves the scored target. The replay-derived (generative) oracle is what makes "
             "this regime free — the fresh answer is re-derived per seed with no "
             "re-annotation — which is the whole reason a generative oracle+golden "
             "*contributes* to contamination resistance rather than just costing more.")
    L.append("- **The boundary is scored-target equivariance, not the domain.** Same DB, "
             "same regenerator; the only difference between R2 and R3 is what gets scored. "
             "That is precondition 5, demonstrated.\n")
    L.append("## The decision rule\n")
    L.append("> Regenerating benchmark state defeats contamination **only if the scored "
             "target co-varies with the regenerated state** and the oracle is re-derived on "
             "that state (a replay/generative oracle makes this free). If the scored "
             "artifact is state-invariant (a program graded by execution), regeneration is "
             "cosmetic against a leak. Score the state, derive the golden by replay.\n")
    L.append("Cross-reference — the IN side, live: on tau-bench branch-selection the "
             "state-equivariant regime opens a **0.44-0.72** gap against the verbatim "
             "replayer A0 (`SOUNDNESS_AUDIT.md`, `DESIGN.md`), and a policy-following agent "
             "grounds on the regenerated world rather than its weights "
             "(`SHIPPED_ABLATION.md`). This receipt is the OUT side that makes it a boundary.")

    Path(args.out).write_text("\n".join(L) + "\n")
    print(f"leaked-query mean={q_mean:.3f}  leaked-answer mean={a_mean:.3f}")
    for i, inst in enumerate(INSTANCES):
        print(f"  Q{i}: R2={q_pass[i]/n:.3f} R3={a_pass[i]/n:.3f} moved={changed[i]/n:.3f}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
