from fastapi import FastAPI, HTTPException

from app.env import AICodeReviewEnvironment
from app.models import ResetRequest, ResetResponse, StateResponse, StepRequest, StepResult

app = FastAPI(
    title="Synapse Code Auditor",
    description="OpenEnv-compatible environment for deterministic AI code review evaluation.",
    version="1.0.0",
)

env = AICodeReviewEnvironment()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "service": "synapse-code-auditor"}


@app.post("/reset", response_model=ResetResponse)
def reset(request: ResetRequest) -> ResetResponse:
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
