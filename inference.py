import json
import os
import time
from dataclasses import dataclass
from typing import Any

import requests
from openai import OpenAI

from app.main import app

try:
    from fastapi.testclient import TestClient
except Exception:  # pragma: no cover
    TestClient = None

TASK_IDS: list[str] = ["easy", "medium", "hard"]


@dataclass
class TaskRun:
    task_id: str
    score: float
    rationale: str
    latency_s: float


class _TestResponse:
    def __init__(self, status_code: int, payload: dict[str, Any]) -> None:
        self.status_code = status_code
        self._payload = payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"Request failed with status {self.status_code}: {self._payload}")

    def json(self) -> dict[str, Any]:
        return self._payload


class _InProcessSession:
    def __init__(self) -> None:
        if TestClient is None:
            raise RuntimeError("fastapi test client is unavailable in this environment")
        self._client = TestClient(app)

    def post(self, path: str, json_payload: dict[str, Any]) -> _TestResponse:
        response = self._client.post(path, json=json_payload)
        return _TestResponse(response.status_code, response.json())


def _emit(tag: str, payload: dict[str, Any]) -> None:
    # Strict tag-prefixed structured logs for evaluator parsing.
    print(f"[{tag}] {json.dumps(payload, separators=(',', ':'), ensure_ascii=True)}", flush=True)


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _build_prompt(task_id: str, instructions: str, code: str) -> str:
    return (
        "You are a code reviewer. Complete exactly the requested review task.\n"
        f"Task ID: {task_id}\n"
        f"Instructions: {instructions}\n"
        "Code:\n"
        f"{code}\n\n"
        "Return concise, actionable review feedback."
    )


def _dry_run_review(task_id: str) -> str:
    if task_id == "easy":
        return (
            "There is a syntax error: missing colon in the function definition. "
            "Fix with def add_numbers(a, b):"
        )
    if task_id == "medium":
        return (
            "Use a list comprehension to preserve behavior and improve readability: "
            "return [n * n for n in numbers if n % 2 == 0]."
        )
    return (
        "Code review: handle empty list to prevent division by zero, avoid broad except Exception, "
        "iterate directly over values, add type hints and tests. Overall score: 0.86/1.0."
    )


def _run_task(env_base_url: str, client: OpenAI, model_name: str, task_id: str, dry_run: bool) -> TaskRun:
    t0 = time.perf_counter()

    if env_base_url == "inprocess":
        session = _InProcessSession()
        reset_response = session.post("/reset", {"task_id": task_id, "seed": 42})
    else:
        reset_response = requests.post(
            f"{env_base_url}/reset",
            json={"task_id": task_id, "seed": 42},
            timeout=30,
        )
    reset_response.raise_for_status()
    observation = reset_response.json()["observation"]

    if dry_run:
        review = _dry_run_review(task_id)
    else:
        prompt = _build_prompt(
            task_id=observation["task_id"],
            instructions=observation["instructions"],
            code=observation["code"],
        )
        completion = client.chat.completions.create(
            model=model_name,
            temperature=0,
            seed=42,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert software engineer specializing in code review.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        review = completion.choices[0].message.content or ""

    if env_base_url == "inprocess":
        step_response = session.post("/step", {"action": {"review": review}})
    else:
        step_response = requests.post(
            f"{env_base_url}/step",
            json={"action": {"review": review}},
            timeout=30,
        )
    step_response.raise_for_status()
    reward = step_response.json()["reward"]

    return TaskRun(
        task_id=task_id,
        score=float(reward["score"]),
        rationale=str(reward["rationale"]),
        latency_s=round(time.perf_counter() - t0, 3),
    )


def main() -> None:
    start_ts = int(time.time())
    env_base_url = os.getenv("ENV_BASE_URL", "http://localhost:7860")
    api_base_url = _required_env("API_BASE_URL")
    model_name = _required_env("MODEL_NAME")
    hf_token = _required_env("HF_TOKEN")
    dry_run = os.getenv("DRY_RUN", "0") == "1"

    _emit(
        "START",
        {
            "event": "run_started",
            "timestamp": start_ts,
            "env_base_url": env_base_url,
            "api_base_url": api_base_url,
            "model_name": model_name,
            "task_count": len(TASK_IDS),
            "dry_run": dry_run,
        },
    )

    client = OpenAI(base_url=api_base_url, api_key=hf_token)

    results: list[TaskRun] = []
    for index, task_id in enumerate(TASK_IDS, start=1):
        result = _run_task(env_base_url, client, model_name, task_id, dry_run)
        results.append(result)
        _emit(
            "STEP",
            {
                "event": "task_completed",
                "index": index,
                "task_id": result.task_id,
                "score": result.score,
                "rationale": result.rationale,
                "latency_s": result.latency_s,
            },
        )

    avg_score = round(sum(item.score for item in results) / len(results), 4)
    total_latency = round(sum(item.latency_s for item in results), 3)

    _emit(
        "END",
        {
            "event": "run_finished",
            "timestamp": int(time.time()),
            "average_score": avg_score,
            "total_latency_s": total_latency,
            "tasks": [{"task_id": r.task_id, "score": r.score} for r in results],
            "status": "ok",
        },
    )


if __name__ == "__main__":
    main()
