"""AppWorld independent-domain A0 gap (QA tasks, answer-swap).

For each scenario with a shipped _1/_2/_3 orbit (same task template, regenerated
state), a contaminated A0 adversary that memorized instance i's answer is scored on
instance j by completing j's task with i's answer and running j's own replay-derived
evaluation. Own-answer = soundness baseline (each instance solvable, oracle correct);
cross-answer = the memorization gap. State-based oracle, no LLM.
"""
import os, json, sys, itertools
os.environ.setdefault("APPWORLD_ROOT", "/Users/junekim/Documents/appworld-work")
from appworld import AppWorld

ROOT = "/Users/junekim/Documents/appworld-work"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 30

def ans(tid):
    p = f"{ROOT}/data/tasks/{tid}/ground_truth/answer.json"
    return json.load(open(p))

def has_answer(tid):
    try:
        a = ans(tid)
        return a is not None and a != "" and a != -1000
    except Exception:
        return False

def grade(task_id, answer):
    with AppWorld(task_id=task_id, experiment_name="a0_qa", load_ground_truth=True) as w:
        w.execute(f"apis.supervisor.complete_task(status='success', answer={json.dumps(answer)})")
        return bool(getattr(w.evaluate(), "success", False))

# collect QA scenarios from train+dev with a full 3-instance orbit, distinct answers
ids = []
for split in ("train", "dev"):
    ids += open(f"{ROOT}/data/datasets/{split}.txt").read().split()
scen = {}
for tid in ids:
    base, _, k = tid.rpartition("_")
    scen.setdefault(base, []).append(tid)
qa_scen = []
for base, insts in scen.items():
    insts = sorted(insts)
    if len(insts) >= 2 and all(has_answer(t) for t in insts):
        answers = [ans(t) for t in insts]
        if len(set(map(str, answers))) == len(answers):   # distinct answers across orbit
            qa_scen.append(insts)
qa_scen = qa_scen[:N]
print(f"QA scenarios with distinct-answer orbit: using {len(qa_scen)}", flush=True)

own_pass = own_tot = cross_pass = cross_tot = 0
for insts in qa_scen:
    for j, tj in enumerate(insts):
        # baseline: own answer
        if grade(tj, ans(tj)): own_pass += 1
        own_tot += 1
        # A0: sibling's answer (next in orbit)
        ti = insts[(j + 1) % len(insts)]
        if grade(tj, ans(ti)): cross_pass += 1
        cross_tot += 1
    print(f"  {insts[0].rpartition('_')[0]}: own {own_pass}/{own_tot} cross {cross_pass}/{cross_tot}", flush=True)

print(f"\nOWN-ANSWER (soundness)  pass = {own_pass}/{own_tot} = {own_pass/own_tot:.3f}")
print(f"CROSS-ANSWER (A0 gap)   pass = {cross_pass}/{cross_tot} = {cross_pass/cross_tot:.3f}")
