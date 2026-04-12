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
    # Align with grader clamp [0.01, 0.99]. Using ge/le makes OpenAPI emit
    # minimum/maximum 0.01/0.99 — not exclusiveMinimum 0.0 / exclusiveMaximum 1.0,
    # which some hub validators misread as forbidden score literals.
    score: float = Field(ge=0.01, le=0.99)
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
    last_reward: float | None = Field(default=None, ge=0.01, le=0.99)
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
    # Explicit flag for static validators / hub scanners that inspect task definitions.
    has_grader: bool = True


class GradeResult(BaseModel):
    score: float = Field(ge=0.01, le=0.99)
    matched_criteria: list[str]
    missed_criteria: list[str]
    penalties: dict[str, float]
    rationale: str
