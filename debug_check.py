import math
from app.grader import normalize_score, grade_review
from app.tasks import TASKS

# ---- normalize_score edge cases ----
print("=== normalize_score edge cases ===")
print(f"normalize_score(nan)  = {normalize_score(float('nan'))}")
print(f"normalize_score(inf)  = {normalize_score(float('inf'))}")
print(f"normalize_score(-inf) = {normalize_score(float('-inf'))}")
print(f"normalize_score(0.0)  = {normalize_score(0.0)}")
print(f"normalize_score(1.0)  = {normalize_score(1.0)}")
print(f"normalize_score(1.5)  = {normalize_score(1.5)}")
print(f"normalize_score(0.5)  = {normalize_score(0.5)}")

# ---- coverage=1.0 edge case ----
print()
print("=== coverage=1.0 edge case ===")
task = TASKS["easy"]
full_review = "sql injection parameterized query f-string interpolation prepared statement"
result = grade_review(task, full_review)
raw_coverage = len(result.matched_criteria) / max(len(task.criteria), 1)
print(f"Easy full-match: score={result.score}, matched={len(result.matched_criteria)}/{len(task.criteria)}, raw_coverage={raw_coverage}")

# ---- Empty review ----
print()
print("=== Empty / minimal review ===")
for label, rev in [("empty", ""), ("single char", "a"), ("30 spaces", "   " * 30)]:
    try:
        r = grade_review(task, rev)
        print(f"  [{label}] score={r.score}  finite={math.isfinite(r.score)}")
    except Exception as e:
        print(f"  [{label}] raised: {e}")

# ---- Extreme reviews on all tasks ----
print()
print("=== All tasks, extreme inputs ===")
junk = ("weather recipe movie travel football politics unrelated filler text "
        "with enough tokens to avoid the too_short penalty entirely here")
emptyish = "a " * 30
inputs = {"junk": junk, "emptyish": emptyish, "syntax_error_repeat": "syntax error " * 20}
for task_id, task in TASKS.items():
    for label, rev in inputs.items():
        r = grade_review(task, rev)
        s = float(r.score)
        ok = math.isfinite(s) and 0.0 < s < 1.0
        print(f"  task={task_id} input={label} score={s} OK={ok}")

# ---- Validator's own check ----
print()
print("=== Validator normalize_score assertions ===")
assert normalize_score(float("nan")) == 0.99, f"FAIL: {normalize_score(float('nan'))}"
assert normalize_score(float("inf")) == 0.99, f"FAIL: {normalize_score(float('inf'))}"
assert normalize_score(0.0) == 0.01, f"FAIL: {normalize_score(0.0)}"
assert normalize_score(1.0) == 0.99, f"FAIL: {normalize_score(1.0)}"
assert normalize_score(1.5) == 0.99, f"FAIL: {normalize_score(1.5)}"
print("All assertions passed!")
