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


def _normalize(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9_+.#-]+", text.lower()))


def _contains_phrase(text: str, phrase: str) -> bool:
    return phrase.lower() in text


def grade_review(task: TaskDefinition, review: str) -> GradeResult:
    normalized_review = _normalize(review)

    matched_criteria: list[str] = []
    missed_criteria: list[str] = []

    for criterion_group in task.criteria:
        matched = any(_contains_phrase(normalized_review, _normalize(phrase)) for phrase in criterion_group)
        canonical = criterion_group[0]
        if matched:
            matched_criteria.append(canonical)
        else:
            missed_criteria.append(canonical)

    coverage_score = len(matched_criteria) / len(task.criteria)

    penalties: dict[str, float] = {}

    if len(review.split()) < 12:
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

    total_penalty = sum(penalties.values())
    final_score = max(0.0, min(1.0, coverage_score - total_penalty))

    rationale = (
        f"Coverage={coverage_score:.2f}; Penalty={total_penalty:.2f}; "
        f"Matched={len(matched_criteria)}/{len(task.criteria)}"
    )

    return GradeResult(
        score=round(final_score, 4),
        matched_criteria=matched_criteria,
        missed_criteria=missed_criteria,
        penalties=penalties,
        rationale=rationale,
    )
