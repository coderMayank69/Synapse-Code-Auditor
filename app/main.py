from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse

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
    }


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
