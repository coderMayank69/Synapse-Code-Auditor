"""
Exhaustive Phase 2 simulation - run every check the hub might run.
"""
import math
import json
from fastapi.testclient import TestClient
from app.grader import grade_review, grader, normalize_score
from app.main import app
from app.tasks import TASKS

ALL_PASS = True

def check(name, cond, detail=""):
    global ALL_PASS
    status = "PASS" if cond else "FAIL"
    if not cond:
        ALL_PASS = False
    print(f"  [{status}] {name}" + (f" | {detail}" if detail else ""))
    return cond

print("=== 1. normalize_score edge cases ===")
check("nan -> 0.99", normalize_score(float("nan")) == 0.99, str(normalize_score(float("nan"))))
check("inf -> 0.99", normalize_score(float("inf")) == 0.99, str(normalize_score(float("inf"))))
check("-inf -> 0.01", normalize_score(float("-inf")) == 0.01, str(normalize_score(float("-inf"))))
check("0.0 -> 0.01", normalize_score(0.0) == 0.01, str(normalize_score(0.0)))
check("1.0 -> 0.99", normalize_score(1.0) == 0.99, str(normalize_score(1.0)))
check("1.5 -> 0.99", normalize_score(1.5) == 0.99, str(normalize_score(1.5)))
check("0.5 -> 0.5", normalize_score(0.5) == 0.5, str(normalize_score(0.5)))

print()
print("=== 2. Task count and grader presence ===")
check(">=3 tasks", len(TASKS) >= 3, str(len(TASKS)))
for tid, task in TASKS.items():
    check(f"{tid} has_grader=True", task.has_grader is True)

print()
print("=== 3. Scoring with grader function ===")
sample_reviews = {
    "easy": "This uses an f-string leading to a sql injection. Use a parameterized query instead.",
    "medium": "Race condition. The await allows interleaving. Use an async lock to make it atomic.",
    "hard": (
        "Blocking requests.post call in an async def function. Handle exceptions properly and "
        "avoid synchronous file i/o. Extract hardcoded urls. Overall score: 0.85 (on a 0-1 scale)."
    ),
}
for task_id, task in TASKS.items():
    review = sample_reviews.get(task_id, "Provide relevant code review feedback with score.")
    result = grade_review(task, review)
    s = float(result.score)
    check(f"{task_id} score in (0,1)", 0.0 < s < 1.0, str(s))
    check(f"{task_id} score is finite", math.isfinite(s), str(s))

print()
print("=== 4. Grader edge cases (all tasks, all junk inputs) ===")
junk = (
    "weather recipe movie travel football politics unrelated filler text "
    "with enough tokens to avoid the too_short penalty entirely here"
)
emptyish = "a " * 30
for task_id, task in TASKS.items():
    for label, rev in [("junk", junk), ("emptyish", emptyish), ("syntax_error_repeat", "syntax error " * 20)]:
        result = grade_review(task, rev)
        s = float(result.score)
        check(f"{task_id}/{label} finite", math.isfinite(s), str(s))
        check(f"{task_id}/{label} in (0,1)", 0.0 < s < 1.0, str(s))
        gs = grader(rev, task)
        check(f"{task_id}/{label} grader==grade_review", gs == s, f"grader={gs} grade_review={s}")

print()
print("=== 5. API contract checks ===")
client = TestClient(app)

r = client.get("/health")
check("/health 200", r.status_code == 200, str(r.status_code))

r = client.get("/metadata")
data = r.json()
check("/metadata 200", r.status_code == 200)
check("metadata tasks >= 3", len(data.get("tasks", [])) >= 3, str(len(data.get("tasks", []))))
graded = sum(1 for t in data["tasks"] if t.get("has_grader") is True or t.get("grader_enabled") is True)
check("metadata graded >= 3", graded >= 3, str(graded))
with_grader_obj = sum(1 for t in data["tasks"] if isinstance(t.get("grader"), dict) and t["grader"].get("enabled") is True)
check("metadata grader.enabled >= 3", with_grader_obj >= 3, str(with_grader_obj))
meta_graders = data.get("graders", [])
check("metadata.graders >= 3", len(meta_graders) >= 3, str(len(meta_graders)))
enabled_meta = sum(1 for g in meta_graders if isinstance(g, dict) and g.get("enabled") is True)
check("metadata.graders enabled >= 3", enabled_meta >= 3, str(enabled_meta))
nested = (data.get("grading") or {}).get("graders", [])
check("metadata.grading.graders >= 3", len(nested) >= 3, str(len(nested)))
nested_enabled = sum(1 for g in nested if isinstance(g, dict) and g.get("enabled") is True)
check("metadata.grading.graders enabled >= 3", nested_enabled >= 3, str(nested_enabled))

r2 = client.get("/tasks")
tdata = r2.json()
check("/tasks 200", r2.status_code == 200)
tlist = tdata.get("tasks", [])
check("/tasks count >= 3", len(tlist) >= 3, str(len(tlist)))
n = sum(1 for t in tlist if t.get("has_grader") is True and isinstance(t.get("grader"), dict) and t["grader"].get("enabled") is True)
check("/tasks enabled deterministic graders >= 3", n >= 3, str(n))
for t in tlist:
    if isinstance(t, dict):
        raw = json.dumps(t)
        has_bad_float = '"score":0.0' in raw or '"score": 0.0' in raw or '"score":1.0' in raw or '"score": 1.0' in raw
        check(f"/tasks/{t.get('task_id')} no 0.0/1.0 float", not has_bad_float, raw[:100])

r3 = client.get("/graders.json")
gdata = r3.json()
check("/graders.json >= 3 graders", len(gdata.get("graders", [])) >= 3, str(len(gdata.get("graders", []))))
enabled_g = sum(1 for g in gdata.get("graders", []) if isinstance(g, dict) and g.get("enabled") is True)
check("/graders.json enabled >= 3", enabled_g >= 3, str(enabled_g))

print()
print("=== 6. Reset + Step flow ===")
reset_r = client.post("/reset", json={})
check("/reset 200", reset_r.status_code == 200)
obs = reset_r.json()["observation"]
check("observation has task_id", "task_id" in obs)
check("observation has code", "code" in obs)
check("observation has instructions", "instructions" in obs)

step_r = client.post("/step", json={"action": {"review": "There is an sql injection vulnerability. Fix using a parameterized query."}})
check("/step 200", step_r.status_code == 200)
sbody = step_r.json()
raw_step = json.dumps(sbody)
bad_floats = any(x in raw_step for x in ['"score":0.0', '"score": 0.0', '"score":1.0', '"score": 1.0'])
check("/step no 0.0/1.0 float", not bad_floats)
reward = sbody.get("reward", {})
score_val = float(reward.get("score", -1.0))
check("/step score in (0,1)", 0.0 < score_val < 1.0, str(score_val))

state_r = client.get("/state")
check("/state 200", state_r.status_code == 200)
state_body = state_r.json()
raw_state = json.dumps(state_body)
bad_state = any(x in raw_state for x in ['"score":0.0', '"score": 0.0', '"score":1.0', '"score": 1.0'])
check("/state no 0.0/1.0 float", not bad_state)

print()
print("=== 7. OpenAPI schema ===")
oa_r = client.get("/openapi.json")
raw_oa = json.dumps(oa_r.json())
check("no exclusiveMinimum 0.0", '"exclusiveMinimum": 0.0' not in raw_oa)
check("no exclusiveMaximum 1.0", '"exclusiveMaximum": 1.0' not in raw_oa)
reward_schema = oa_r.json()["components"]["schemas"]["Reward"]["properties"]["score"]
check("Reward.score minimum=0.01", reward_schema.get("minimum") == 0.01, str(reward_schema))
check("Reward.score maximum=0.99", reward_schema.get("maximum") == 0.99, str(reward_schema))

print()
if ALL_PASS:
    print("ALL CHECKS PASSED")
else:
    print("SOME CHECKS FAILED")
