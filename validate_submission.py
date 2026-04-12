from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from app.grader import grade_review
from app.main import app
from app.tasks import TASKS


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
        1 for t in tasks if isinstance(t, dict) and t.get("grader") is True
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

    state = client.get("/state")
    assert state.status_code == 200, f"/state returned {state.status_code}"


def _check_tasks_and_graders() -> None:
    assert len(TASKS) >= 3, "At least 3 tasks are required"

    sample_reviews = {
        "easy": "Syntax error due to missing colon after function definition. Use def add_numbers(a, b):",
        "medium": "Use a list comprehension while preserving behavior for readability and concise code.",
        "hard": (
            "Handle empty list to avoid division by zero, avoid broad except Exception, "
            "iterate directly, add type hints/tests, overall score: 0.85/1.0."
        ),
    }

    for task_id, task in TASKS.items():
        review = sample_reviews.get(task_id, "Provide relevant code review feedback with score.")
        result = grade_review(task, review)
        assert 0.0 < result.score < 1.0, f"Score out of strict range for {task_id}: {result.score}"


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
    _check_metadata_graders()
    _check_api_contracts()
    _check_tasks_and_graders()
    _check_inference_script(root / "inference.py")
    _run_inference_dry_run(root)

    print(json.dumps({"status": "ok", "message": "Pre-submission validation passed."}))


if __name__ == "__main__":
    main()
