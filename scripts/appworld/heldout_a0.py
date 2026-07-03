"""Held-out A0 gap: the method run on GENUINELY FRESH state.

heldout2 contains instances regenerated at a held-out seed (12345) that never shipped:
new users, new answers, oracle re-derived by replay (validated at generation time).
A model "contaminated" on the SHIPPED benchmark memorized the shipped answers. We score:
  own-answer (fresh)  : complete a held-out task with its OWN fresh answer -> soundness of
                        the replay oracle on state that did not exist before.
  A0 shipped-answer   : complete a held-out task with the SHIPPED answer (memorized) ->
                        the memorization gap on fresh state.
Only QA scenarios (answers present in both). State-based oracle, no LLM.
"""
import os, json, sys
os.environ["APPWORLD_ROOT"] = "/Users/junekim/Documents/appworld-work/heldout2"
from appworld import AppWorld

HELD = "/Users/junekim/Documents/appworld-work/heldout2/data"
SHIP = "/Users/junekim/Documents/appworld-work/v2root/data"

def ans(root, tid):
    return json.load(open(f"{root}/tasks/{tid}/ground_truth/answer.json"))

def grade(task_id, answer):
    with AppWorld(task_id=task_id, experiment_name="heldout_a0", load_ground_truth=True) as w:
        w.execute(f"apis.supervisor.complete_task(status='success', answer={json.dumps(answer)})")
        return bool(getattr(w.evaluate(), "success", False))

# held-out task ids present, grouped
held_ids = sorted(os.listdir(f"{HELD}/tasks"))
own_pass = own_tot = a0_pass = a0_tot = 0
rows = []
for tid in held_ids:
    try:
        a_held = ans(HELD, tid)
        a_ship = ans(SHIP, tid)   # shipped counterpart (same id, shipped state)
    except Exception:
        continue
    if a_held in (None, "", -1000) or a_ship in (None, "", -1000):
        continue
    own = grade(tid, a_held)                       # soundness on fresh state
    a0 = grade(tid, a_ship) if str(a_ship) != str(a_held) else None  # memorized-shipped
    own_pass += int(own); own_tot += 1
    if a0 is not None:
        a0_pass += int(a0); a0_tot += 1
    rows.append((tid, a_held, a_ship, own, a0))
    print(f"  {tid}: own(fresh)={own}  A0(shipped)={a0}  held={a_held!r} ship={a_ship!r}", flush=True)

print(f"\nHELD-OUT SOUNDNESS (own fresh answer)  = {own_pass}/{own_tot} = {own_pass/max(own_tot,1):.3f}")
print(f"A0 MEMORIZED-SHIPPED on fresh state    = {a0_pass}/{a0_tot} = {a0_pass/max(a0_tot,1):.3f}"
      if a0_tot else "A0: no distinct-answer pairs")
