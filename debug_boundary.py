"""
Simulate what the HUB Phase 2 validator might specifically check vs local validator.
Check for the hidden score=0.99 clamped boundary trap.
"""
import math

# --- Critical: When coverage_score == 1.0 exact and no penalties ---
# raw_score = 1.0 - 0 = 1.0
# normalize_score(round(1.0, 4)) = normalize_score(1.0) = 0.99
# This is SAFE for API Pydantic validation (ge=0.01, le=0.99)
# But the hub might check EXCLUSIVE bounds: score < 1.0

# What if the hub calls /step with a PERFECT review and checks score < 1.0?
from fastapi.testclient import TestClient
from app.main import app
from app.tasks import TASKS
from app.grader import grade_review

client = TestClient(app)

print("=== Perfect review scenarios (all criteria matched, no penalties) ===")
# Easy: criteria = sql injection, parameterized query, f-string
perfect_easy = (
    "This code has a critical sql injection vulnerability via f-string string interpolation. "
    "The fix is to use a parameterized query / prepared statement with bind variables."
)

# Medium: criteria = race condition, lock/mutex/transaction, .sleep/await/interleaving
perfect_medium = (
    "This has a race condition data race concurrency issue. The await asyncio.sleep causes "
    "interleaving between concurrent calls. Use an async lock mutex or database transaction to ensure atomicity."
)

# Hard: criteria = blocking/synchronous/requests.post, file i/o/aiofiles, error handling/exception, 
#        hardcoded/config/environment variable, overall score/rating
perfect_hard = (
    "Blocking synchronous call with requests.post in async def function ruins concurrency. "
    "File i/o with open audit log should use aiofiles. Error handling via try/except needed when res.json() fails. "
    "Hardcoded http://internal-log.local should use environment variable config. "
    "Overall score: 0.72 rating for this endpoint."
)

for task_id, review in [("easy", perfect_easy), ("medium", perfect_medium), ("hard", perfect_hard)]:
    task = TASKS[task_id]
    result = grade_review(task, review)
    s = float(result.score)
    print(f"  {task_id}: score={s}, matched={len(result.matched_criteria)}/{len(task.criteria)}, penalties={result.penalties}")
    print(f"    strict (0<s<1): {0.0 < s < 1.0}")
    print(f"    is 0.99: {s == 0.99}")

print()
print("=== Checking if /step can ever return exactly 0.0 or 1.0 ===")
# Reset and step with perfect review
for task_id, review in [("easy", perfect_easy), ("medium", perfect_medium), ("hard", perfect_hard)]:
    client.post("/reset", json={"task_id": task_id, "seed": 42})
    step_r = client.post("/step", json={"action": {"review": review}})
    reward = step_r.json()["reward"]
    s = float(reward["score"])
    print(f"  {task_id} API score={s}, in(0,1)={0.0<s<1.0}, ne 0.0: {s!=0.0}, ne 1.0: {s!=1.0}")

print()
print("=== Score range boundary test ===")
# The Pydantic model uses ge=0.01, le=0.99
# If hub uses EXCLUSIVE bounds (>0, <1), 0.01 and 0.99 are still OK
# But 0.0 and 1.0 must NEVER appear
print("Pydantic Reward model: ge=0.01 le=0.99 -> min/max in OpenAPI = 0.01/0.99")
print("Hub requirement: 0 < score < 1 (exclusive)")
print("Our range [0.01, 0.99] satisfies 0 < score < 1: YES")
print("Edge: score=0.01 -> 0 < 0.01 < 1: TRUE")  
print("Edge: score=0.99 -> 0 < 0.99 < 1: TRUE")
