# Project Guidelines

## Code Style
- Use Python 3.11 and type hints for all public functions.
- Keep request/response schemas in Pydantic models under app/models.py.
- Keep grading deterministic; avoid non-deterministic scoring logic.

## Architecture
- FastAPI entrypoint is app/main.py.
- Core environment logic is app/env.py with reset, step, and state methods.
- Task definitions live in app/tasks.py.
- Deterministic reward logic lives in app/grader.py.

## Build and Test
- Install dependencies: pip install -r requirements.txt
- Run API server: uvicorn app.main:app --host 0.0.0.0 --port 8000
- Validate OpenEnv manifest: openenv validate
- Run baseline script: python app/inference.py
- Build and run container:
  - docker build -t synapse-code-auditor .
  - docker run --rm -p 8000:8000 synapse-code-auditor

## Conventions
- Environment episodes are single-step for scoring consistency.
- Reward must remain within 0.0 to 1.0 with partial credit support.
- API schema compatibility for endpoints /reset, /step, and /state is required.
