# Synapse Code Auditor (OpenEnv Environment)

Synapse Code Auditor is a production-ready OpenEnv environment for evaluating AI code-review behavior across deterministic tasks.

## Real-World Use Case

Software teams use code review to catch bugs, improve quality, and enforce maintainability. This environment simulates that workflow so agent performance can be trained and measured with reproducible rewards.

## Project Structure

```text
.
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
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. Validate OpenEnv manifest

```bash
openenv validate
```

## Docker Run

```bash
docker build -t synapse-code-auditor .
docker run --rm -p 8000:8000 synapse-code-auditor
```

Then test:

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/reset -H "Content-Type: application/json" -d "{\"task_id\":\"easy\",\"seed\":42}"
```

## Baseline Inference Script

The baseline runner uses an OpenAI-compatible client and executes all 3 tasks.

Required environment variables:

- OPENAI_API_KEY: API key for model inference
- API_BASE_URL: OpenAI-compatible API URL (default https://api.openai.com/v1)
- MODEL_NAME: model identifier (default gpt-4o-mini)

Optional:

- ENV_BASE_URL: environment API base URL (default http://localhost:8000)

Run:

```bash
python app/inference.py
```

## Example Baseline Output

```text
Synapse Code Auditor baseline run
Environment URL: http://localhost:8000
Model endpoint: https://api.openai.com/v1
Model: gpt-4o-mini
- easy: score=1.0000 | Coverage=1.00; Penalty=0.00; Matched=3/3
- medium: score=1.0000 | Coverage=1.00; Penalty=0.00; Matched=3/3
- hard: score=0.8000 | Coverage=1.00; Penalty=0.20; Matched=5/5
Average score: 0.9333
```

## Hugging Face Spaces Deployment

This project is container-ready and compatible with Hugging Face Docker Spaces.

1. Push repository to Hugging Face Space configured for Docker.
2. Ensure port 8000 is exposed (already set in Dockerfile and openenv.yaml).
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
