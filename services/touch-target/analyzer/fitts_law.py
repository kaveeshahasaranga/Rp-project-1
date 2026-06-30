"""
Fitts's Law index-of-difficulty analyser for touch targets.

Fitts's Law (1954) predicts the time required to move to a target:
    MT = a + b * log2(2D / W)

The Index of Difficulty (ID) portion ``log2(2D / W)`` is used here as a
proxy for the acquisition difficulty of a touch target.  For a 2-D target
we treat:
    * W  = min(width, height)   — the narrower dimension constrains accuracy
    * 2D = 2 * max(width, height) — approximation when distance is unknown

This gives:
    ID = log2(2 * max_dim / min_dim)

Higher ID → harder to hit → worse user experience.

Reference: Fitts, P.M. (1954). The information capacity of the human motor system in
controlling the amplitude of movement. Journal of Experimental Psychology, 47(6), 381–391.
"""

from __future__ import annotations

import logging
import math

logger = logging.getLogger(__name__)

# Empirically determined threshold above which a target is considered "difficult"
ID_VIOLATION_THRESHOLD: float = 3.5


def compute_id(width: float, height: float) -> float:
    """
    Compute the Fitts's Law Index of Difficulty for a rectangular target.

    Uses the simplified formula:
        ID = log2(2 × max(w, h) / max(min(w, h), 1))

    Both arguments must be non-negative.  Very small dimensions (< 1 px)
    are clamped to 1 to avoid division-by-zero or negative log results.

    Parameters
    ----------
    width:
        Target width in CSS pixels.
    height:
        Target height in CSS pixels.

    Returns
    -------
    float
        Index of Difficulty (higher = harder to acquire).
        Returns 0.0 for degenerate inputs (w == h, i.e. perfectly square).
    """
    w = max(float(width), 1.0)
    h = max(float(height), 1.0)
    max_dim = max(w, h)
    min_dim = min(w, h)
    if min_dim <= 0:
        return 0.0
    return math.log2((2.0 * max_dim) / min_dim)


def analyze_fitts_compliance(elements: list[dict]) -> dict:
    """
    Compute Fitts's Law metrics across all interactive elements.

    Parameters
    ----------
    elements:
        List of element dicts with at least ``width`` and ``height`` fields.
        Elements with zero area are skipped (likely hidden / collapsed).

    Returns
    -------
    dict
        Keys:
        * ``mean_id``              — float, mean Index of Difficulty
        * ``max_id``               — float, maximum ID in the set
        * ``violations``           — list of element dicts where ID > threshold
        * ``fitts_compliance_score``
            float in [0, 100]; 100 = all targets easy, 0 = all impossible.
        * ``id_violation_threshold`` — float, threshold used (3.5)
    """
    scored: list[tuple[dict, float]] = []

    for el in elements:
        w = float(el.get("width", 0))
        h = float(el.get("height", 0))
        if w <= 0 or h <= 0:
            continue  # skip invisible / collapsed elements
        id_val = compute_id(w, h)
        scored.append((el, id_val))

    if not scored:
        return {
            "mean_id": 0.0,
            "max_id": 0.0,
            "violations": [],
            "fitts_compliance_score": 100.0,
            "id_violation_threshold": ID_VIOLATION_THRESHOLD,
        }

    ids = [s[1] for s in scored]
    mean_id = float(sum(ids) / len(ids))
    max_id = float(max(ids))

    violations = [
        {**el, "index_of_difficulty": round(id_val, 4)}
        for el, id_val in scored
        if id_val > ID_VIOLATION_THRESHOLD
    ]

    # Score: proportion of elements that do NOT violate the threshold
    passing = len(scored) - len(violations)
    fitts_score = round((passing / len(scored)) * 100.0, 2)

    logger.info(
        "Fitts analysis: mean_id=%.3f  max_id=%.3f  violations=%d  score=%.1f",
        mean_id, max_id, len(violations), fitts_score,
    )

    return {
        "mean_id": round(mean_id, 4),
        "max_id": round(max_id, 4),
        "violations": violations,
        "fitts_compliance_score": fitts_score,
        "id_violation_threshold": ID_VIOLATION_THRESHOLD,
    }
