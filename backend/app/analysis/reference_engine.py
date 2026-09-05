"""Deterministic reference-range engine and comparison logic."""

from __future__ import annotations

import re


class ReferenceStatusResult(str):
    """String subclass that treats LOW==BELOW and HIGH==ABOVE for full backward compatibility."""

    def __eq__(self, other: object) -> bool:
        if super().__eq__(other):
            return True
        s = str(self)
        if s in ("LOW", "BELOW") and other in ("LOW", "BELOW"):
            return True
        if s in ("HIGH", "ABOVE") and other in ("HIGH", "ABOVE"):
            return True
        return False

    def __hash__(self) -> int:
        return super().__hash__()


def parse_reference_range(text: str | None) -> tuple[float | None, float | None]:
    """Parse a reference range string like '13-17', '13 - 17', '13.0 - 17.0 g/dL', '< 200', '> 40' etc.

    Returns (low, high). Either may be None if not determinable.
    """
    if not text:
        return None, None

    text = text.strip().replace(",", "")

    # If compound with '|', prefer desirable / optimal / normal / low risk / adult part
    if "|" in text:
        parts = [p.strip() for p in text.split("|")]
        chosen = parts[0]
        for p in parts:
            if any(k in p.lower() for k in ("desirable", "optimal", "normal", "low risk", "adult")):
                chosen = p
                break
        text = chosen

    # Remove leading words like "Reference Range:", "Reference:", "Normal:", "Adult:", "Desirable Level:", etc.
    text = re.sub(
        r"^(?:(?:biological\s+)?reference\s+(?:range|interval)s?|normal\s+ranges?|expected\s+ranges?|ref\.?\s*(?:range|interval)s?|reference|ref|adults?|desirable(?:\s*level)?|optimal|normal|low\s*risk)\s*[:=\-]?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()

    # Remove trailing unit suffixes like "g/dL", "mg/dL", "cells/uL", "cells/µL", "%", etc.
    text = re.sub(r"[a-zA-Z/%µ\s]+$", "", text).strip()

    # Range: "13-17", "13 - 17", "13–17", "13 to 17"
    range_match = re.match(r"(\d+(?:\.\d+)?)\s*(?:-|–|—|\bto\b)\s*(\d+(?:\.\d+)?)", text, re.IGNORECASE)
    if range_match:
        return float(range_match.group(1)), float(range_match.group(2))

    # Less than: "< 200", "<= 200", "<200", "Up to 200"
    lt_match = re.match(r"[<≤]=?\s*(\d+(?:\.\d+)?)", text)
    if lt_match:
        return None, float(lt_match.group(1))

    up_to_match = re.match(r"up\s*to\s*(\d+(?:\.\d+)?)", text, re.IGNORECASE)
    if up_to_match:
        return None, float(up_to_match.group(1))

    # Greater than: "> 40", ">= 40", ">40"
    gt_match = re.match(r"[>≥]=?\s*(\d+(?:\.\d+)?)", text)
    if gt_match:
        return float(gt_match.group(1)), None

    return None, None


def calculate_reference_status(
    value_numeric: float | None,
    reference_low: float | None,
    reference_high: float | None,
) -> ReferenceStatusResult:
    """Deterministic reference-range calculation.

    For numeric results:
      if lower <= observed <= upper: WITHIN
      if observed < lower: LOW
      if observed > upper: HIGH

    Returns: ReferenceStatusResult ("WITHIN", "LOW", "HIGH", or "UNKNOWN").
    """
    if value_numeric is None:
        return ReferenceStatusResult("UNKNOWN")

    if reference_low is not None and reference_high is not None:
        if value_numeric < reference_low:
            return ReferenceStatusResult("LOW")
        elif value_numeric > reference_high:
            return ReferenceStatusResult("HIGH")
        else:
            return ReferenceStatusResult("WITHIN")

    if reference_low is not None and reference_high is None:
        # "> X" or ">= X" — value should be at or above this threshold
        if value_numeric < reference_low:
            return ReferenceStatusResult("LOW")
        return ReferenceStatusResult("WITHIN")

    if reference_high is not None and reference_low is None:
        # "< X" or "<= X" — value should be at or below this threshold
        if value_numeric > reference_high:
            return ReferenceStatusResult("HIGH")
        return ReferenceStatusResult("WITHIN")

    return ReferenceStatusResult("UNKNOWN")



def parse_numeric_value(value: str) -> float | None:
    """Try to extract a numeric value from a string like '10.2', '> 1000', '5,400'."""
    if not value:
        return None
    cleaned = value.strip().replace(",", "")
    # Remove leading operators
    cleaned = re.sub(r"^[<>≤≥=~]+\s*", "", cleaned)
    try:
        return float(cleaned)
    except ValueError:
        return None


def calculate_change_direction(
    prev_numeric: float | None,
    curr_numeric: float | None,
    prev_unit: str | None,
    curr_unit: str | None,
) -> tuple[str, float | None, float | None]:
    """Calculate change direction and magnitude between two values.

    Returns: (direction, absolute_change, percentage_change)
    """
    # Units must match for comparison
    if prev_unit and curr_unit and prev_unit.strip().lower() != curr_unit.strip().lower():
        return "NOT_COMPARABLE", None, None

    if prev_numeric is None and curr_numeric is not None:
        return "NEW", None, None

    if prev_numeric is not None and curr_numeric is None:
        return "MISSING", None, None

    if prev_numeric is None or curr_numeric is None:
        return "NOT_COMPARABLE", None, None

    absolute = round(curr_numeric - prev_numeric, 4)
    percentage = round((absolute / prev_numeric) * 100, 2) if prev_numeric != 0 else None

    if abs(absolute) < 0.001:
        return "STABLE", 0.0, 0.0

    if absolute > 0:
        return "INCREASED", absolute, percentage

    return "DECREASED", absolute, percentage
