# AppWorld independent-domain experiment — reproduction

AppWorld (Stony Brook, ACL 2024) is the independent second domain (proof-ladder step 6).
It is a local tool-agent benchmark (9 apps, FastAPI + SQLite), graded by a deterministic
state-diff over the app databases. Data/code live OUTSIDE this repo (~180 MB); only these
scripts and the receipt (`docs/receipts/APPWORLD_INDEPENDENT.md`) are tracked here.

## One-time setup (done in ~/Documents/appworld-work)

```bash
uv venv --python 3.13 .venv
VIRTUAL_ENV=.venv uv pip install appworld           # base package
# repo (for the task GENERATORS, which are not in the pip package):
GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 https://github.com/StonyBrookNLP/appworld.git repo
cd repo && git lfs pull                              # real .source/*.bundle (generators, gen code)
VIRTUAL_ENV=../.venv uv pip install -e '.[all]'      # repo == 0.2.0.dev0; brings ruff, generate deps
.../.venv/bin/appworld install --repo                # unpack encrypted bundles -> generate/tasks/...
# v0.2.0 data (base catalog + shipped tasks) into a root:
APPWORLD_ROOT=../v2root .../.venv/bin/appworld download data
```

Gotchas (all real, all cost an hour if unknown — see docs/WORKLOG.md):
- generators ship as git-LFS `.source/*.bundle`; skip-smudge clone leaves pointers → `git lfs pull`.
- `generate/` is not on sys.path → run with `PYTHONPATH=<repo>`.
- generation refuses to run unless `PYTHONHASHSEED` is set (repro guard).
- generated-task save shells out to `ruff` → put `<venv>/bin` on `PATH` or it exits 127.
- pip data is db-version 0.1.0; repo code is 0.2.0.dev0 and rejects it → download v0.2.0 data.

## Regenerate at a held-out seed (the method run)

Produces a fresh orbit (new users + answers, oracle re-derived by replay) into a root that
symlinks the v0.2.0 base catalog so the shipped orbit is not clobbered:

```bash
mkdir -p heldout2/data/tasks && cd heldout2/data
for d in base_dbs api_docs datasets; do ln -s ../../v2root/data/$d $d; done
cp ../../v2root/data/version.txt .
cd repo
PATH=../.venv/bin:$PATH PYTHONHASHSEED=12345 PYTHONPATH=. APPWORLD_ROOT=../heldout2 \
  ../.venv/bin/python generate/tasks/generate_and_validate_tasks.py \
  "82e2fac,692c77d,2a163ab,6104387,29caf6f,afc0fce,287e338,27e1026,22cc237,d0b1f43,b7a9ee9,76f2c72" \
  --generator_num_tasks 3 --use_environment --use_compiled_solution --random_seed 12345 --suppress_errors
```
`>> Passed (12)` means every scenario regenerated AND its reference solution reaches its
regenerated replay-derived oracle — soundness of the generative oracle on fresh state.

## Measure the gap

- `heldout_a0.py` — over the held-out QA instances: own-fresh-answer pass (soundness on fresh
  state) vs memorized-SHIPPED-answer pass (the A0 gap). Reports collisions (shipped==held).
- `appworld_a0_qa.py` — the shipped-orbit breadth version (cross-instance answer-swap over
  the shipped `_1/_2/_3` orbit). Weaker; kept as breadth.

Paths inside the scripts point at ~/Documents/appworld-work/{v2root,heldout2}; adjust if
you relocate the working tree.
