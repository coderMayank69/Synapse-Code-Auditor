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
)
from app.tasks import TASKS

# Repo root (contains openenv.yaml) — /app in Docker, project dir locally.
_ENV_ROOT = Path(__file__).resolve().parent.parent
_OPENENV_PATH = _ENV_ROOT / "openenv.yaml"

app = FastAPI(
    title="Synapse Code Auditor",
    description="OpenEnv-compatible environment for deterministic AI code review evaluation.",
    version="1.0.0",
)

env = AICodeReviewEnvironment()


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
    return {
        "name": app.title,
        "description": app.description,
        "version": app.version,
        "task_count": len(TASKS),
        "tasks": [
            {
                "task_id": task.id,
                "task_type": task.task_type.value,
                "has_grader": True,
                "grader_enabled": True,
                "criteria_count": len(task.criteria),
            }
            for task in TASKS.values()
        ],
        "grading": {
            "type": "automated",
            "deterministic": True,
            "tasks_with_graders": len(TASKS),
        },
    }


@app.get("/tasks")
def list_tasks() -> dict[str, Any]:
    """Task catalog with grader flags (used by hub validators and OpenEnv clients)."""
    return {
        "task_count": len(TASKS),
        "tasks": [
            {
                "task_id": task.id,
                "task_type": task.task_type.value,
                "title": task.title,
                "has_grader": True,
                "grader": {"type": "deterministic", "enabled": True},
                # Use numeric bounds strictly inside (0, 1); some validators reject
                # any 0.0/1.0 floats anywhere under task payloads.
                "score_range": [0.01, 0.99],
            }
            for task in TASKS.values()
        ],
    }


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
