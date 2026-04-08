---
title: Synapse Code Auditor
emoji: "⚡"
colorFrom: red
colorTo: pink
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: Code reviewer environment
---

# Synapse Code Auditor (OpenEnv Environment)

Synapse Code Auditor is a production-ready OpenEnv environment for evaluating AI code-review behavior across deterministic tasks.

## Real-World Use Case

Software teams use code review to catch bugs, improve quality, and enforce maintainability. This environment simulates that workflow so agent performance can be trained and measured with reproducible rewards.

## Project Structure

```text
.
├── server/
│   ├── __init__.py
│   └── app.py
├── inference.py
├── pyproject.toml
├── uv.lock
├── validate_submission.py
├── app/
│   ├── __init__.py
│   ├── env.py
│   ├── grader.py
│   ├── inference.py
│   ├── main.py
│   ├── models.py
│   └── tasks.py
├── .dockerignore
├── Dockerfile
├── openenv.yaml
├── README.md
└── requirements.txt
```

## OpenEnv Interface

This environment implements the required interface methods in the core environment class:

- reset(task_id=None, seed=42)
- step(action)
- state()

FastAPI endpoints expose the same functionality:

- POST /reset
- POST /step
- GET /state

## Action and Observation Schemas

Observation:

```json
{
  "task_id": "easy",
  "task_type": "easy",
  "code": "def add_numbers(a, b)\n    result = a + b\n    return result\n",
  "instructions": "Identify the exact syntax error in the code and propose a valid fix.",
  "previous_feedback": null
}
```

Action:

```json
{
  "review": "The function definition is missing a colon. Change it to def add_numbers(a, b):"
}
```

Reward:

```json
{
  "score": 1.0,
  "matched_criteria": ["syntax error", "missing colon", "def add_numbers(a, b):"],
  "missed_criteria": [],
  "penalties": {},
  "rationale": "Coverage=1.00; Penalty=0.00; Matched=3/3"
}
```

## Tasks

1. Easy: Detect syntax errors
2. Medium: Suggest optimization
3. Hard: Full code review with scoring

Each task has deterministic grading criteria and a score range of 0.0 to 1.0.

## Deterministic Grader and Reward Design

- Deterministic keyword/criterion matching for each task.
- Partial reward from criterion coverage.
- Penalties for short, irrelevant, or incorrect responses.
- Hard task penalizes missing overall score/rating in the review.

Reward formula:

```text
score = clamp(criterion_coverage - penalties, 0.0, 1.0)
```

## Local Setup

### 1. Create environment and install dependencies

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
```

### 2. Run FastAPI server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 7860
```

### 3. Validate OpenEnv manifest

```bash
openenv validate
```

## Docker Run

```bash
docker build -t synapse-code-auditor .
docker run --rm -p 7860:7860 synapse-code-auditor
```

Then test:

```bash
curl http://localhost:7860/health
curl -X POST http://localhost:7860/reset -H "Content-Type: application/json" -d "{\"task_id\":\"easy\",\"seed\":42}"
```

## Baseline Inference Script

The baseline runner is `inference.py` at the project root. It uses the OpenAI client and executes all 3 tasks.

Required environment variables for non-dry-run execution:

- API_BASE_URL: OpenAI-compatible API URL
- MODEL_NAME: model identifier
- HF_TOKEN: API key used by OpenAI client

Optional:

- ENV_BASE_URL: environment API base URL (default http://localhost:7860)
- DRY_RUN: set to `1` to skip external LLM calls and use deterministic local responses
- API_BASE_URL: defaults to https://api.openai.com/v1 when not provided
- MODEL_NAME: defaults to gpt-4o-mini when not provided

Structured logs:

- `[START]` one event at run start
- `[STEP]` one event per task
- `[END]` one event at run finish

Run:

```bash
python inference.py
```

### Required env var example

```bash
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-4o-mini"
export HF_TOKEN="your_token_here"
export ENV_BASE_URL="http://localhost:7860"
python inference.py
```

### Pre-submission validator

```bash
python validate_submission.py
```

Validator checks:

- OpenEnv manifest keys
- `/health`, `/reset`, `/step`, `/state` endpoint behavior
- 3+ tasks and grader output range in `[0.0, 1.0]`
- root `inference.py` requirements and structured logs

## Example Baseline Output

```text
[START] {"event":"run_started","env_base_url":"inprocess","task_count":3,"dry_run":true}
[STEP] {"event":"task_completed","index":1,"task_id":"easy","score":1.0}
[STEP] {"event":"task_completed","index":2,"task_id":"medium","score":1.0}
[STEP] {"event":"task_completed","index":3,"task_id":"hard","score":0.9}
[END] {"event":"run_finished","average_score":0.9667,"status":"ok"}
```

## Hugging Face Spaces Deployment

This project is container-ready and compatible with Hugging Face Docker Spaces.

1. Push repository to Hugging Face Space configured for Docker.
2. Ensure port 7860 is exposed (already set in Dockerfile and openenv.yaml).
3. Build and run automatically in Space.

OpenEnv deployment command:

```bash
openenv push
```

## API Reference

- GET /health
- POST /reset with payload {"task_id": "easy|medium|hard", "seed": 42}
- POST /step with payload {"action": {"review": "..."}}
- GET /state

This environment is ready for end-to-end local execution, Docker execution, and OpenEnv workflow validation.
