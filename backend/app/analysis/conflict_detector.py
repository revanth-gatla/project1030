"""Deterministic conflict detection engine."""

from __future__ import annotations


def detect_allergy_conflict(
    current_allergies: str | None,
    previous_allergies: str | None,
) -> list[dict]:
    """Detect potential allergy conflicts between intake and previous records."""
    conflicts = []
    if not current_allergies and not previous_allergies:
        return conflicts

    curr = (current_allergies or "").strip().lower()
    prev = (previous_allergies or "").strip().lower()

    if not curr and not prev:
        return conflicts

    # "No known allergies" vs actual allergies
    no_allergy_phrases = ["no known allergies", "nka", "nkda", "none", "nil", "no allergies"]
    curr_is_none = any(p in curr for p in no_allergy_phrases) or not curr
    prev_is_none = any(p in prev for p in no_allergy_phrases) or not prev

    if curr_is_none and not prev_is_none and prev:
        conflicts.append({
            "conflict_type": "ALLERGY",
            "description": "Current intake indicates no known allergies, but a previous record lists allergies.",
            "source_a": f"Current intake: {current_allergies or 'No allergies listed'}",
            "source_b": f"Previous record: {previous_allergies}",
            "severity": "HIGH",
        })
    elif not curr_is_none and prev_is_none and curr:
        conflicts.append({
            "conflict_type": "ALLERGY",
            "description": "Current intake lists allergies, but a previous record indicates no known allergies.",
            "source_a": f"Current intake: {current_allergies}",
            "source_b": f"Previous record: {previous_allergies or 'No allergies listed'}",
            "severity": "MEDIUM",
        })

    return conflicts


def detect_medication_conflict(
    current_medications: str | None,
    previous_medications: str | None,
) -> list[dict]:
    """Detect potential medication discrepancies."""
    conflicts = []
    if not current_medications and not previous_medications:
        return conflicts

    curr_set = _extract_items(current_medications)
    prev_set = _extract_items(previous_medications)

    if not curr_set or not prev_set:
        return conflicts

    # Find medications in previous but not in current
    discontinued = prev_set - curr_set
    if discontinued:
        conflicts.append({
            "conflict_type": "MEDICATION",
            "description": f"Medications from a previous record not listed in the current intake: {', '.join(sorted(discontinued))}. Verify if these were intentionally discontinued.",
            "source_a": f"Current medications: {current_medications}",
            "source_b": f"Previous medications: {previous_medications}",
            "severity": "MEDIUM",
        })

    return conflicts


def detect_demographic_conflict(
    current_age: int | None,
    previous_age: int | None,
    current_sex: str | None,
    previous_sex: str | None,
) -> list[dict]:
    """Detect potential demographic inconsistencies."""
    conflicts = []

    if current_age is not None and previous_age is not None:
        if abs(current_age - previous_age) > 5:
            conflicts.append({
                "conflict_type": "DEMOGRAPHIC",
                "description": f"Age discrepancy detected: current record shows {current_age}, previous record shows {previous_age}.",
                "source_a": f"Current age: {current_age}",
                "source_b": f"Previous age: {previous_age}",
                "severity": "MEDIUM",
            })

    if current_sex and previous_sex:
        if current_sex.upper() != previous_sex.upper() and current_sex.upper() != "UNKNOWN" and previous_sex.upper() != "UNKNOWN":
            conflicts.append({
                "conflict_type": "DEMOGRAPHIC",
                "description": "Sex/gender discrepancy detected between records.",
                "source_a": f"Current: {current_sex}",
                "source_b": f"Previous: {previous_sex}",
                "severity": "HIGH",
            })

    return conflicts


def detect_duplicate_parameters(lab_results: list[dict]) -> list[dict]:
    """Detect potentially duplicate parameters after normalization."""
    conflicts = []
    canonical_counts: dict[str, list[dict]] = {}

    for lr in lab_results:
        name = lr.get("canonical_name", "").lower()
        if name not in canonical_counts:
            canonical_counts[name] = []
        canonical_counts[name].append(lr)

    for name, entries in canonical_counts.items():
        if len(entries) > 1:
            originals = [e.get("original_name", "") for e in entries]
            conflicts.append({
                "conflict_type": "DUPLICATE_PARAMETER",
                "description": f"Multiple entries found for '{entries[0].get('canonical_name', name)}': {', '.join(originals)}. These may represent the same parameter.",
                "source_a": f"{originals[0]}: {entries[0].get('observed_value', '')}",
                "source_b": f"{originals[-1]}: {entries[-1].get('observed_value', '')}",
                "severity": "LOW",
            })

    return conflicts


def _extract_items(text: str | None) -> set[str]:
    """Extract individual items from a comma/newline separated string."""
    if not text:
        return set()
    items = set()
    for part in text.replace("\n", ",").split(","):
        cleaned = part.strip().lower()
        if cleaned and cleaned not in ("none", "nil", "n/a", "na", "-"):
            items.add(cleaned)
    return items
