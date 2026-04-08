from app.grader import grade_review
from app.models import Action, EnvState, Observation, Reward, StepResult, TaskType
from app.tasks import ORDERED_TASK_IDS, get_task


class AICodeReviewEnvironment:
    def __init__(self) -> None:
        self.episode_id = 0
        self.total_steps = 0
        self._task_pointer = 0
        self._last_reward: float | None = None
        self._history: list[dict] = []
        self._current_task_id: str | None = None
        self._current_observation: Observation | None = None
        self._done = False

    def reset(self, task_id: str | None = None, seed: int = 42) -> Observation:
        self.episode_id += 1
        self._done = False

        if task_id is None:
            # Deterministic task sequence controlled by seed for reproducibility.
            self._task_pointer = (seed + self.episode_id - 1) % len(ORDERED_TASK_IDS)
            chosen_task_id = ORDERED_TASK_IDS[self._task_pointer]
        else:
            chosen_task_id = task_id

        task = get_task(chosen_task_id)

        observation = Observation(
            task_id=task.id,
            task_type=TaskType(task.task_type),
            code=task.code,
            instructions=task.instructions,
            previous_feedback=None,
        )

        self._current_task_id = task.id
        self._current_observation = observation
        return observation

    def step(self, action: Action) -> StepResult:
        if self._current_task_id is None or self._current_observation is None:
            raise ValueError("Environment not initialized. Call reset() first.")

        if self._done:
            raise ValueError("Episode already completed. Call reset() for a new task.")

        task = get_task(self._current_task_id)
        grade = grade_review(task=task, review=action.review)

        reward = Reward(
            score=grade.score,
            matched_criteria=grade.matched_criteria,
            missed_criteria=grade.missed_criteria,
            penalties=grade.penalties,
            rationale=grade.rationale,
        )

        self.total_steps += 1
        self._done = True
        self._last_reward = reward.score

        self._history.append(
            {
                "episode_id": self.episode_id,
                "task_id": task.id,
                "task_type": task.task_type,
                "reward": reward.score,
            }
        )

        next_observation = Observation(
            task_id=self._current_observation.task_id,
            task_type=self._current_observation.task_type,
            code=self._current_observation.code,
            instructions=self._current_observation.instructions,
            previous_feedback=f"Scored {reward.score:.2f}. {reward.rationale}",
        )

        return StepResult(
            observation=next_observation,
            reward=reward,
            done=True,
            info={
                "task_title": task.title,
                "episode_id": self.episode_id,
            },
        )

    def state(self) -> EnvState:
        status = "idle" if self._current_task_id is None else ("done" if self._done else "awaiting_action")
        current_type = None
        if self._current_task_id is not None:
            current_type = get_task(self._current_task_id).task_type

        return EnvState(
            episode_id=self.episode_id,
            current_task_id=self._current_task_id,
            current_task_type=current_type,
            status=status,
            total_steps=self.total_steps,
            last_reward=self._last_reward,
            history=self._history[-20:],
        )
