from app.models import TaskDefinition, TaskType


TASKS: dict[str, TaskDefinition] = {
    "easy": TaskDefinition(
        id="easy",
        task_type=TaskType.EASY,
        title="Detect syntax errors",
        code=(
            "def add_numbers(a, b)\n"
            "    result = a + b\n"
            "    return result\n"
        ),
        instructions=(
            "Identify the exact syntax error in the code and propose a valid fix. "
            "The response should mention the specific line-level issue and corrected syntax."
        ),
        criteria=[
            ["syntax error", "invalid syntax"],
            ["missing colon", "colon after function definition", "def line needs colon"],
            ["def add_numbers(a, b):", "add a colon at end of function definition"],
        ],
    ),
    "medium": TaskDefinition(
        id="medium",
        task_type=TaskType.MEDIUM,
        title="Suggest optimization",
        code=(
            "def squared_evens(numbers):\n"
            "    result = []\n"
            "    for n in numbers:\n"
            "        if n % 2 == 0:\n"
            "            result.append(n * n)\n"
            "    return result\n"
        ),
        instructions=(
            "Suggest performance or readability optimizations while preserving behavior. "
            "Mention at least one concrete optimization strategy and why it helps."
        ),
        criteria=[
            ["list comprehension", "comprehension"],
            ["same behavior", "preserve behavior", "without changing output"],
            ["readability", "cleaner", "more concise"],
        ],
    ),
    "hard": TaskDefinition(
        id="hard",
        task_type=TaskType.HARD,
        title="Full code review with scoring",
        code=(
            "def average(values):\n"
            "    total = 0\n"
            "    for i in range(len(values)):\n"
            "        total += values[i]\n"
            "    return total / len(values)\n\n"
            "def process(data):\n"
            "    try:\n"
            "        return [average(x) for x in data]\n"
            "    except Exception:\n"
            "        return []\n"
        ),
        instructions=(
            "Perform a full code review covering correctness, robustness, efficiency, and maintainability. "
            "Include an explicit overall score in the review."
        ),
        criteria=[
            ["division by zero", "empty list", "len(values) == 0"],
            ["broad exception", "except Exception", "too broad catch"],
            ["iterate directly", "avoid range(len", "pythonic loop"],
            ["type hints", "docstring", "tests"],
            ["overall score", "score", "rating"],
        ],
    ),
}


ORDERED_TASK_IDS: list[str] = ["easy", "medium", "hard"]


def get_task(task_id: str) -> TaskDefinition:
    if task_id not in TASKS:
        raise KeyError(f"Unknown task_id: {task_id}")
    return TASKS[task_id]
