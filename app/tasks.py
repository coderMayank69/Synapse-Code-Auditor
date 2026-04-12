from app.models import TaskDefinition, TaskType


TASKS: dict[str, TaskDefinition] = {
    "easy": TaskDefinition(
        id="easy",
        task_type=TaskType.EASY,
        has_grader=True,
        title="Detect SQL Injection Vulnerability",
        code=(
            "def authenticate_user(username, password, db_cursor):\n"
            "    query = f\"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'\"\n"
            "    db_cursor.execute(query)\n"
            "    return db_cursor.fetchone()\n"
        ),
        instructions=(
            "Identify the critical security vulnerability in this authentication code and propose a secure fix. "
            "Mention the exact vulnerability name and standard mitigation technique."
        ),
        criteria=[
            ["sql injection", "sqli", "injection attack"],
            ["parameterized query", "prepared statement", "bind variables", "pass as parameters"],
            ["f-string", "string formatting", "interpolation"],
        ],
    ),
    "medium": TaskDefinition(
        id="medium",
        task_type=TaskType.MEDIUM,
        has_grader=True,
        title="Identify Async Race Condition",
        code=(
            "import asyncio\n\n"
            "async def update_balance(user_id, amount, db_client):\n"
            "    balance = await db_client.get_balance(user_id)\n"
            "    new_balance = balance + amount\n"
            "    await asyncio.sleep(0.05)  # Simulate latency\n"
            "    await db_client.set_balance(user_id, new_balance)\n"
        ),
        instructions=(
            "Review this asynchronous money transfer logic. Identify the concurrency bug, "
            "explain why it occurs, and suggest a robust solution."
        ),
        criteria=[
            ["race condition", "data race", "concurrency issue"],
            ["lock", "mutex", "transaction", "atomic"],
            [".sleep", "await", "interleaving"],
        ],
    ),
    "hard": TaskDefinition(
        id="hard",
        task_type=TaskType.HARD,
        has_grader=True,
        title="Comprehensive FastAPI Endpoint Review",
        code=(
            "from fastapi import FastAPI\n"
            "import requests\n"
            "import json\n\n"
            "app = FastAPI()\n\n"
            "@app.post('/webhook')\n"
            "def handle_webhook(payload: dict):\n"
            "    if not payload.get('user_id'): return {'error': 'missing id'}\n"
            "    res = requests.post('http://internal-log.local/audit', json=payload)\n"
            "    with open('audit.log', 'a') as f:\n"
            "        f.write(json.dumps(res.json()) + '\\n')\n"
            "    return {'status': 'processed'}\n"
        ),
        instructions=(
            "Perform a comprehensive code review covering performance, architecture, resilience, and correctness. "
            "Include an explicit overall score in the review."
        ),
        criteria=[
            ["blocking", "synchronous call", "requests.post", "async def", "httpx"],
            ["file i/o", "blocking i/o", "open('audit.log", "aiofiles"],
            ["error handling", "exception", "res.json() fails", "status code", "try/except"],
            ["hardcoded", "config", "environment variable", "http://internal-log.local"],
            ["overall score", "score", "rating", "final score", "overall rating"],
        ],
    ),
}


ORDERED_TASK_IDS: list[str] = ["easy", "medium", "hard"]

# Explicit curriculum ordering for multi-task episodes and static validators.
ORDERED_TASK_DEFINITIONS: list[TaskDefinition] = [TASKS[tid] for tid in ORDERED_TASK_IDS]


def get_task(task_id: str) -> TaskDefinition:
    if task_id not in TASKS:
        raise KeyError(f"Unknown task_id: {task_id}")
    return TASKS[task_id]
