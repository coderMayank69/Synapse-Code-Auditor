import math
import re

from app.models import GradeResult, TaskDefinition


_IRRELEVANT_MARKERS = {
    "weather",
    "recipe",
    "movie",
    "travel",
    "football",
    "politics",
}

_MIN_SCORE = 0.01
_MAX_SCORE = 0.99


def normalize_score(score: float) -> float:
    """Clamp score to (0.01, 0.99). Handles NaN, Inf, and any non-finite value safely.

    This is the MANDATORY safe scoring function required by the Phase 2 validator.
    It guarantees: 0 < result < 1, strictly between 0 and 1 (never 0.0 or 1.0).
    """
    try:
        v = float(score)
    except (TypeError, ValueError):
        return _MIN_SCORE
    # Explicit NaN / Inf guard before clamping — nan comparisons are always False,
    # which means max/min with nan can silently propagate nan on some platforms.
    if not math.isfinite(v):
        # Positive infinity (or nan treated as high) -> cap at max safe value.
        # Negative infinity -> floor at min safe value.
        return _MAX_SCORE if v > 0 or math.isnan(v) else _MIN_SCORE
    return max(_MIN_SCORE, min(_MAX_SCORE, v))


def _normalize(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9_+.#-]+", text.lower()))


def _contains_phrase(text: str, phrase: str) -> bool:
    return phrase.lower() in text


def grade_review(task: TaskDefinition, review: str) -> GradeResult:
    normalized_review = _normalize(review)
    n_groups = len(task.criteria)
    if n_groups == 0:
        return GradeResult(
            score=normalize_score(0.5),
            matched_criteria=[],
            missed_criteria=[],
            penalties={"no_criteria": 0.5},
            rationale="No grading criteria configured; neutral partial score.",
        )

    matched_criteria: list[str] = []
    missed_criteria: list[str] = []

    for criterion_group in task.criteria:
        matched = any(_contains_phrase(normalized_review, _normalize(phrase)) for phrase in criterion_group)
        canonical = criterion_group[0]
        if matched:
            matched_criteria.append(canonical)
        else:
            missed_criteria.append(canonical)

    # Clamp coverage to avoid floating-point representation reaching exactly 1.0.
    coverage_score = len(matched_criteria) / n_groups  # range: [0.0, 1.0]

    penalties: dict[str, float] = {}

    words = review.split()
    if len(words) < 12:
        penalties["too_short"] = 0.15

    if len(matched_criteria) == 0:
        penalties["no_relevant_content"] = 0.35

    if re.search(r"\b(no issues|looks good|perfect as is)\b", review.lower()):
        penalties["incorrect_no_issues_claim"] = 0.30

    irrelevant_hits = sum(1 for marker in _IRRELEVANT_MARKERS if marker in normalized_review)
    if irrelevant_hits >= 2:
        penalties["irrelevant_content"] = min(0.10 * irrelevant_hits, 0.30)

    if task.id == "hard" and not re.search(r"\b(score|rating|overall)\b", review.lower()):
        penalties["missing_overall_score"] = 0.10

    total_penalty = min(sum(penalties.values()), coverage_score + 0.50)  # prevent over-penalization
    # Scale coverage into (0.05, 0.95) before penalty to leave headroom from boundaries.
    # This prevents a perfect review from reaching 1.0 or a junk review from reaching 0.0.
    scaled_coverage = 0.05 + coverage_score * 0.90  # maps [0,1] -> [0.05, 0.95]
    raw_score = scaled_coverage - (total_penalty * 0.90)
    score = normalize_score(round(raw_score, 4))

    cov_display = min(coverage_score, _MAX_SCORE)
    rationale = (
        f"Coverage={cov_display:.2f}; Penalty={total_penalty:.2f}; "
        f"Matched={len(matched_criteria)}/{n_groups}"
    )

    return GradeResult(
        score=score,
        matched_criteria=matched_criteria,
        missed_criteria=missed_criteria,
        penalties=penalties,
        rationale=rationale,
    )


def compute_score(output: str, expected: TaskDefinition) -> float:
    result = grade_review(expected, output)
    return result.score


def grader(output: str, expected: TaskDefinition) -> float:
    score = compute_score(output, expected)
    return normalize_score(score)
