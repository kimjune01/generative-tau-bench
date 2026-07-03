"""Boundary OUT side on held-out state: does a SHIPPED state-general procedure survive
regeneration? For every held-out instance, run the SHIPPED compiled solution against the
HELD-OUT world and grade. High survival = procedures are state-invariant (regeneration does
NOT defeat procedure-level memorization) AND the held-out tasks are solvable on fresh state
(specificity control). Pairs with the QA concrete-answer IN side (heldout_a0.py)."""
import os, json
os.environ["APPWORLD_ROOT"] = "/Users/junekim/Documents/appworld-work/heldout2"
from appworld import AppWorld

HELD = "/Users/junekim/Documents/appworld-work/heldout2/data"
SHIP = "/Users/junekim/Documents/appworld-work/v2root/data"

def is_qa(tid):
    a = json.load(open(f"{HELD}/tasks/{tid}/ground_truth/answer.json"))
    return a not in (None, "", -1000)

ids = sorted(os.listdir(f"{HELD}/tasks"))
pass_n = crash_n = fail_n = 0
by = {"qa": [0, 0], "mut": [0, 0]}   # [survive, total]
for tid in ids:
    shipped = f"{SHIP}/tasks/{tid}/ground_truth/compiled_solution.py"
    if not os.path.exists(shipped):
        continue
    code = open(shipped).read()
    survived = False
    status = "fail"
    try:
        with AppWorld(task_id=tid, experiment_name="proc_survival", load_ground_truth=True) as w:
            out = w.execute(code + "\nsolution(apis=apis, requester=requester)")
            crashed = "Execution failed" in str(out) or "Traceback" in str(out)
            ok = bool(getattr(w.evaluate(), "success", False))
            if crashed and not ok:
                status = "crash"
            elif ok:
                status = "pass"; survived = True
            else:
                status = "fail"
    except Exception as e:
        status = "crash"
    k = "qa" if is_qa(tid) else "mut"
    by[k][1] += 1; by[k][0] += int(survived)
    pass_n += int(status == "pass"); crash_n += int(status == "crash"); fail_n += int(status == "fail")
    print(f"  {tid} [{k}]: {status}", flush=True)

tot = pass_n + crash_n + fail_n
print(f"\nSHIPPED PROCEDURE ON HELD-OUT WORLD (n={tot})")
print(f"  survives (pass) = {pass_n}/{tot} = {pass_n/max(tot,1):.3f}")
print(f"  completed-but-wrong = {fail_n}   crashed = {crash_n}")
print(f"  by class: QA {by['qa'][0]}/{by['qa'][1]}   mutation {by['mut'][0]}/{by['mut'][1]}")
