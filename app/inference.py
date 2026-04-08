import os
from dataclasses import dataclass

import requests
from openai import OpenAI


@dataclass
class BaselineResult:
    task_id: str
    score: float
    rationale: str


def _build_prompt(task_id: str, instructions: str, code: str) -> str:
    return (
        "You are a code reviewer. Complete exactly the requested review task.\n"
        f"Task ID: {task_id}\n"
        f"Instructions: {instructions}\n"
        "Code:\n"
        f"{code}\n\n"
        "Return concise, actionable review feedback."
    )


def _run_task(
    env_base_url: str,
    client: OpenAI,
    model_name: str,
    task_id: str,
) -> BaselineResult:
    reset_response = requests.post(
        f"{env_base_url}/reset",
        json={"task_id": task_id, "seed": 42},
        timeout=30,
    )
    reset_response.raise_for_status()
    reset_payload = reset_response.json()

    observation = reset_payload["observation"]
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

    step_response = requests.post(
        f"{env_base_url}/step",
        json={"action": {"review": review}},
        timeout=30,
    )
    step_response.raise_for_status()
    step_payload = step_response.json()

    return BaselineResult(
        task_id=task_id,
        score=float(step_payload["reward"]["score"]),
        rationale=step_payload["reward"]["rationale"],
    )


def main() -> None:
    env_base_url = os.getenv("ENV_BASE_URL", "http://localhost:8000")
    api_base_url = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
    model_name = os.getenv("MODEL_NAME", "gpt-4o-mini")
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY must be set to run inference.py")

    client = OpenAI(base_url=api_base_url, api_key=api_key)

    task_ids = ["easy", "medium", "hard"]
    results = [_run_task(env_base_url, client, model_name, task_id) for task_id in task_ids]

    print("Synapse Code Auditor baseline run")
    print(f"Environment URL: {env_base_url}")
    print(f"Model endpoint: {api_base_url}")
    print(f"Model: {model_name}")

    total = 0.0
    for result in results:
        total += result.score
        print(f"- {result.task_id}: score={result.score:.4f} | {result.rationale}")

    avg_score = total / len(results)
    print(f"Average score: {avg_score:.4f}")


if __name__ == "__main__":
    main()
