from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

import math

from app.grader import grade_review, grader, normalize_score
from app.main import app
from app.tasks import TASKS


def _floats_bad(obj: object) -> list[float]:
    bad: list[float] = []
    if isinstance(obj, float) and (obj == 0.0 or obj == 1.0):
        bad.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            bad.extend(_floats_bad(v))
    elif isinstance(obj, list):
        for item in obj:
            bad.extend(_floats_bad(item))
    return bad


def _check_openenv_yaml(path: Path) -> None:
    content = path.read_text(encoding="utf-8")
    required = ["spec_version:", "name:", "type:", "runtime:", "app:", "port:"]
    missing = [key for key in required if key not in content]
    if missing:
        raise AssertionError(f"openenv.yaml missing keys: {missing}")

    try:
        import yaml
    except ImportError as exc:  # pragma: no cover
        raise AssertionError("PyYAML is required to validate openenv.yaml structure") from exc

    data = yaml.safe_load(content)
    if not isinstance(data, dict):
        raise AssertionError("openenv.yaml must parse to a mapping")

    tasks = data.get("tasks")
    if not isinstance(tasks, list) or len(tasks) < 3:
        raise AssertionError("openenv.yaml must include a tasks: list with at least 3 entries")

    tasks_with_grader = sum(
        1
        for t in tasks
        if isinstance(t, dict)
        and (t.get("grader") is True or t.get("has_grader") is True)
    )
    grading = data.get("grading")
    nested_graders: list = []
    if isinstance(grading, dict):
        g = grading.get("graders")
        if isinstance(g, list):
            nested_graders = g

    root_graders = data.get("graders")
    root_graders_len = len(root_graders) if isinstance(root_graders, list) else 0

    grader_slots = max(tasks_with_grader, len(nested_graders), root_graders_len)
    if grader_slots < 3:
        raise AssertionError(
            "openenv.yaml must declare graders for at least 3 tasks "
            "(each task: grader: true, top-level graders:, and/or grading.graders)"
        )


def _check_openapi_reward_schema() -> None:
    """Synapse-style checks may scan OpenAPI for 0.0/1.0 on score bounds (see Reward model)."""
    client = TestClient(app)
    r = client.get("/openapi.json")
    assert r.status_code == 200
    raw = json.dumps(r.json())
    # Reject the old Pydantic pattern that embeds 0.0/1.0 as exclusive bounds on score.
    assert '"exclusiveMinimum": 0.0' not in raw and '"exclusiveMaximum": 1.0' not in raw, (
        "OpenAPI must not expose exclusive bounds 0.0/1.0 on scores (hub static validation)"
    )
    data = r.json()
    reward = data["components"]["schemas"]["Reward"]["properties"]["score"]
    assert reward.get("minimum") == 0.01 and reward.get("maximum") == 0.99


def _check_graders_json(path: Path) -> None:
    assert path.is_file(), "graders.json is required at repository root for hub scanners"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data.get("tasks_with_graders", 0) >= 3
    graders = data.get("graders")
    assert isinstance(graders, list) and len(graders) >= 3
    enabled = sum(1 for g in graders if isinstance(g, dict) and g.get("enabled") is True)
    assert enabled >= 3, "graders.json must list at least 3 enabled graders"


def _check_task_definitions_have_grader() -> None:
    for task_id, task in TASKS.items():
        assert task.has_grader is True, f"task {task_id} must have has_grader=True"


def _check_metadata_graders() -> None:
    client = TestClient(app)
    response = client.get("/metadata")
    assert response.status_code == 200, f"/metadata returned {response.status_code}"
    payload = response.json()
    tasks = payload.get("tasks")
    assert isinstance(tasks, list) and len(tasks) >= 3, "metadata.tasks must list at least 3 tasks"
    graded = sum(
        1
        for t in tasks
        if isinstance(t, dict) and (t.get("has_grader") is True or t.get("grader_enabled") is True)
    )
    assert graded >= 3, "metadata must expose at least 3 tasks with graders enabled"
    with_grader_obj = sum(
        1
        for t in tasks
        if isinstance(t, dict)
        and isinstance(t.get("grader"), dict)
        and t["grader"].get("enabled") is True
    )
    assert with_grader_obj >= 3, "metadata.tasks must each expose grader.enabled=true (hub Phase-2)"
    meta_graders = payload.get("graders")
    assert isinstance(meta_graders, list) and len(meta_graders) >= 3, "metadata.graders must list >=3 entries"
    assert sum(1 for g in meta_graders if isinstance(g, dict) and g.get("enabled") is True) >= 3
    nested = (payload.get("grading") or {}).get("graders")
    assert isinstance(nested, list) and len(nested) >= 3
    assert sum(1 for g in nested if isinstance(g, dict) and g.get("enabled") is True) >= 3


def _check_tasks_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/tasks")
    assert response.status_code == 200, f"/tasks returned {response.status_code}"
    payload = response.json()
    task_list = payload.get("tasks")
    assert isinstance(task_list, list) and len(task_list) >= 3, "/tasks must list at least 3 tasks"
    n = sum(
        1
        for t in task_list
        if isinstance(t, dict)
        and t.get("has_grader") is True
        and isinstance(t.get("grader"), dict)
        and t["grader"].get("enabled") is True
    )
    assert n >= 3, "/tasks must declare enabled deterministic graders for at least 3 tasks"

    manifest = client.get("/openenv.yaml")
    assert manifest.status_code == 200, f"/openenv.yaml returned {manifest.status_code}"
    assert b"has_grader:" in manifest.content or b"grader:" in manifest.content

    for t in task_list:
        if isinstance(t, dict) and _floats_bad(t):
            raise AssertionError(
                f"/tasks task payload must not contain 0.0 or 1.0 floats (strict grader rules): {t}"
            )

    gm = client.get("/graders.json")
    assert gm.status_code == 200, f"/graders.json returned {gm.status_code}"
    gdata = gm.json()
    assert len(gdata.get("graders", [])) >= 3


def _check_api_contracts() -> None:
    client = TestClient(app)

    health = client.get("/health")
    assert health.status_code == 200, f"/health returned {health.status_code}"

    reset = client.post("/reset", json={})
    assert reset.status_code == 200, f"/reset returned {reset.status_code}"

    obs = reset.json()["observation"]
    assert "task_id" in obs and "instructions" in obs and "code" in obs

    step = client.post(
        "/step",
        json={
            "action": {
                "review": (
                    "There is a syntax error with a missing colon. "
                    "Fix to def add_numbers(a, b):"
                )
            }
        },
    )
    assert step.status_code == 200, f"/step returned {step.status_code}"
    step_body = step.json()
    if _floats_bad(step_body):
        raise AssertionError(f"/step JSON must not contain float 0.0 or 1.0 anywhere: {step_body}")
    reward = step_body.get("reward") or {}
    score = float(reward.get("score", -1.0))
    assert 0.0 < score < 1.0, f"/step reward score must be strictly in (0, 1), got {reward.get('score')}"

    state = client.get("/state")
    assert state.status_code == 200, f"/state returned {state.status_code}"
    state_body = state.json()
    if _floats_bad(state_body):
        raise AssertionError(f"/state JSON must not contain float 0.0 or 1.0 anywhere: {state_body}")


def _check_tasks_and_graders() -> None:
    assert len(TASKS) >= 3, "At least 3 tasks are required"

    sample_reviews = {
        "easy": "Syntax error due to missing colon after function definition. Use def add_numbers(a, b):",
        "medium": "Use a list comprehension while preserving behavior for readability and concise code.",
        "hard": (
            "Handle empty list to avoid division by zero, avoid broad except Exception, "
            "iterate directly, add type hints/tests, overall score: 0.85 (on a 0–1 scale)."
        ),
    }

    for task_id, task in TASKS.items():
        review = sample_reviews.get(task_id, "Provide relevant code review feedback with score.")
        result = grade_review(task, review)
        assert 0.0 < result.score < 1.0, f"Score out of strict range for {task_id}: {result.score}"


def _check_grader_edge_cases() -> None:
    """Stress grader outputs: no NaN/inf, scores never touch 0.0 or 1.0, grader() matches rubric."""
    assert normalize_score(float("nan")) == 0.01
    assert normalize_score(float("inf")) == 0.01
    assert normalize_score(0.0) == 0.01
    assert normalize_score(1.0) == 0.99
    assert normalize_score(1.5) == 0.99

    junk = (
        "weather recipe movie travel football politics unrelated filler text "
        "with enough tokens to avoid the too_short penalty entirely here"
    )
    emptyish = "a " * 30

    for _task_id, task in TASKS.items():
        for review in (junk, emptyish, "syntax error " * 20):
            result = grade_review(task, review)
            s = float(result.score)
            assert math.isfinite(s), f"non-finite score for {task.id}: {s}"
            assert 0.0 < s < 1.0, f"score out of range for {task.id}: {s}"
            assert grader(review, task) == s


def _check_inference_script(path: Path) -> None:
    assert path.exists(), "Root inference.py is required"
    content = path.read_text(encoding="utf-8")

    required_tokens = [
        "API_BASE_URL",
        "MODEL_NAME",
        "HF_TOKEN",
        "OpenAI(",
        '"START"',
        '"STEP"',
        '"END"',
    ]
    missing = [token for token in required_tokens if token not in content]
    if missing:
        raise AssertionError(f"inference.py missing required tokens: {missing}")


def _run_inference_dry_run(root: Path) -> None:
    env = os.environ.copy()
    env.setdefault("API_BASE_URL", "https://api.openai.com/v1")
    env.setdefault("MODEL_NAME", "gpt-4o-mini")
    env.setdefault("HF_TOKEN", "dummy-token-for-dry-run")
    env.setdefault("ENV_BASE_URL", "inprocess")
    env["DRY_RUN"] = "1"

    proc = subprocess.run(
        [sys.executable, "inference.py"],
        cwd=str(root),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )

    if proc.returncode != 0:
        raise AssertionError(f"inference.py dry run failed: {proc.stderr or proc.stdout}")

    lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    assert any(line.startswith("[START]") for line in lines), "Missing [START] log"
    assert sum(1 for line in lines if line.startswith("[STEP]")) >= 3, "Expected >=3 [STEP] logs"
    assert any(line.startswith("[END]") for line in lines), "Missing [END] log"

    for line in lines:
        if not line.startswith("[STEP]"):
            continue
        payload_text = line.split("]", 1)[1].strip()
        step_payload = json.loads(payload_text)
        score = float(step_payload["score"])
        assert 0.0 < score < 1.0, f"inference STEP score must be strictly in (0, 1), got {score}"


def main() -> None:
    root = Path(__file__).resolve().parent

    _check_openenv_yaml(root / "openenv.yaml")
    _check_graders_json(root / "graders.json")
    _check_task_definitions_have_grader()
    _check_openapi_reward_schema()
    _check_metadata_graders()
    _check_tasks_endpoint()
    _check_api_contracts()
    _check_tasks_and_graders()
    _check_grader_edge_cases()
    _check_inference_script(root / "inference.py")
    _run_inference_dry_run(root)

    print(json.dumps({"status": "ok", "message": "Pre-submission validation passed."}))


if __name__ == "__main__":
    main()
