"""Deep API endpoint checks to diagnose hub phase 2 failures."""
import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# /metadata check
r = client.get("/metadata")
data = r.json()
print("=== /metadata ===")
print(f"task_count: {data['task_count']}")
print(f"tasks_with_graders: {data['grading']['tasks_with_graders']}")
print(f"Number of tasks: {len(data['tasks'])}")
for t in data["tasks"]:
    print(f"  {t['task_id']}: has_grader={t['has_grader']}, grader_enabled={t['grader_enabled']}, grader={t['grader']}")

# /tasks check
print()
r2 = client.get("/tasks")
data2 = r2.json()
print("=== /tasks ===")
for t in data2["tasks"]:
    print(f"  {t['task_id']}: has_grader={t['has_grader']}, grader={t['grader']}")

# /graders.json check
print()
r3 = client.get("/graders.json")
data3 = r3.json()
print("=== /graders.json ===")
print(f"tasks_with_graders: {data3['tasks_with_graders']}")
print(f"graders count: {len(data3['graders'])}")
for g in data3["graders"]:
    print(f"  {g}")

# Full reset + step to see actual score
print()
print("=== reset + step (easy task) ===")
reset = client.post("/reset", json={"task_id": "easy", "seed": 42})
print(f"reset status: {reset.status_code}")

step = client.post("/step", json={"action": {"review": "sql injection parameterized query f-string"}})
print(f"step status: {step.status_code}")
step_data = step.json()
score = step_data["reward"]["score"]
print(f"score: {score}, type: {type(score)}")
print(f"score valid (0<x<1): {0.0 < float(score) < 1.0}")

# Check for bad floats
print()
print("=== checking for 0.0 or 1.0 in step response ===")
raw = json.dumps(step_data)
has_zero = '"score": 0.0' in raw or '"score":0.0' in raw
has_one = '"score": 1.0' in raw or '"score":1.0' in raw
print(f"Has 0.0 score literal: {has_zero}")
print(f"Has 1.0 score literal: {has_one}")
print(f"Raw score field in JSON: '{json.dumps(step_data['reward']['score'])}'")
