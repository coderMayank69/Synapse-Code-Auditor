from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TaskType(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Observation(BaseModel):
    task_id: str
    task_type: TaskType
    code: str
    instructions: str
    previous_feedback: str | None = None


class Action(BaseModel):
    review: str = Field(min_length=1)


class Reward(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    matched_criteria: list[str]
    missed_criteria: list[str]
    penalties: dict[str, float]
    rationale: str


class StepResult(BaseModel):
    observation: Observation
    reward: Reward
    done: bool
    info: dict[str, Any]


class EnvState(BaseModel):
    episode_id: int
    current_task_id: str | None
    current_task_type: TaskType | None
    status: str
    total_steps: int
    last_reward: float | None
    history: list[dict[str, Any]]


class ResetRequest(BaseModel):
    task_id: str | None = Field(default=None, description="Task id: easy, medium, hard")
    seed: int = 42


class StepRequest(BaseModel):
    action: Action


class StateResponse(BaseModel):
    state: EnvState


class ResetResponse(BaseModel):
    observation: Observation
    state: EnvState


class TaskDefinition(BaseModel):
    id: str
    task_type: TaskType
    title: str
    code: str
    instructions: str
    criteria: list[list[str]]


class GradeResult(BaseModel):
    score: float
    matched_criteria: list[str]
    missed_criteria: list[str]
    penalties: dict[str, float]
    rationale: str
