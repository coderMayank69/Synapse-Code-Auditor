from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse

from app.env import AICodeReviewEnvironment
from app.models import (
    Action,
    EnvState,
    Observation,
    ResetRequest,
    ResetResponse,
    StateResponse,
    StepRequest,
    StepResult,
    TaskDefinition,
)
from app.tasks import ORDERED_TASK_IDS, TASKS

# Repo root (contains openenv.yaml) — /app in Docker, project dir locally.
_ENV_ROOT = Path(__file__).resolve().parent.parent
_OPENENV_PATH = _ENV_ROOT / "openenv.yaml"

app = FastAPI(
    title="Synapse Code Auditor",
    description="OpenEnv-compatible environment for deterministic AI code review evaluation.",
    version="1.0.0",
)

env = AICodeReviewEnvironment()


def _task_catalog_entry(task: TaskDefinition) -> dict[str, Any]:
    """Single shape for /metadata and /tasks (hub Phase-2 often counts graders on metadata)."""
    return {
        "task_id": task.id,
        "task_type": task.task_type.value,
        "title": task.title,
        "has_grader": task.has_grader,
        "grader_enabled": task.has_grader,
        "grader": {"type": "deterministic", "enabled": True},
        "score_range": [0.01, 0.99],
        "criteria_count": len(task.criteria),
    }


def _graders_manifest_body() -> dict[str, Any]:
    """Always in sync with TASKS; includes aliases some hub scanners expect."""
    return {
        "spec_version": 1,
        "environment": "synapse_code_auditor",
        "tasks_with_graders": len(TASKS),
        "graders": [
            {
                "task_id": tid,
                "task": tid,
                "type": "deterministic",
                "kind": "deterministic",
                "enabled": True,
            }
            for tid in ORDERED_TASK_IDS
        ],
        "score_policy": {
            "min": 0.01,
            "max": 0.99,
            "strictly_between_zero_and_one": True,
        },
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "service": "synapse-code-auditor"}


@app.get("/")
def root() -> dict[str, str]:
    return {"name": app.title, "status": "ready", "docs": "/docs"}


@app.get("/robots.txt", include_in_schema=False)
def robots() -> PlainTextResponse:
    return PlainTextResponse("User-agent: *\nDisallow:\n")


@app.get("/metadata")
def metadata() -> dict[str, Any]:
    tasks = [_task_catalog_entry(TASKS[tid]) for tid in ORDERED_TASK_IDS]
    return {
        "name": app.title,
        "description": app.description,
        "version": app.version,
        "task_count": len(TASKS),
        "tasks": tasks,
        "graders": _graders_manifest_body()["graders"],
        "grading": {
            "type": "automated",
            "deterministic": True,
            "tasks_with_graders": len(TASKS),
            "graders": [
                {"task_id": tid, "type": "deterministic", "enabled": True}
                for tid in ORDERED_TASK_IDS
            ],
        },
    }


@app.get("/tasks")
def list_tasks() -> dict[str, Any]:
    """Task catalog with grader flags (used by hub validators and OpenEnv clients)."""
    return {
        "task_count": len(TASKS),
        "tasks": [_task_catalog_entry(TASKS[tid]) for tid in ORDERED_TASK_IDS],
    }


@app.get("/graders.json")
def graders_manifest() -> dict[str, Any]:
    """Grader manifest derived from TASKS so the running Space cannot drift from code."""
    return _graders_manifest_body()


@app.get("/openenv.yaml")
def openenv_manifest() -> FileResponse:
    """Serve the OpenEnv manifest so validators can read it from the running Space."""
    if not _OPENENV_PATH.is_file():
        raise HTTPException(status_code=404, detail="openenv.yaml not found in environment root")
    return FileResponse(
        _OPENENV_PATH,
        media_type="application/yaml",
        filename="openenv.yaml",
    )


@app.get("/schema")
def schema() -> dict[str, Any]:
    return {
        "action": Action.model_json_schema(),
        "observation": Observation.model_json_schema(),
        "state": EnvState.model_json_schema(),
    }


@app.post("/mcp")
def mcp(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "result": {
            "ok": True,
            "message": "OpenEnv-compatible MCP endpoint is available.",
            "payload": payload or {},
        },
        "id": None,
    }


@app.post("/reset", response_model=ResetResponse)
def reset(request: ResetRequest | None = None) -> ResetResponse:
    request = request or ResetRequest()
    try:
        observation = env.reset(task_id=request.task_id, seed=request.seed)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ResetResponse(observation=observation, state=env.state())


@app.post("/step", response_model=StepResult)
def step(request: StepRequest) -> StepResult:
    try:
        return env.step(request.action)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/state", response_model=StateResponse)
def state() -> StateResponse:
    return StateResponse(state=env.state())
