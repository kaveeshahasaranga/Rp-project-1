"""
Composite cognitive-load / clutter scorer.

Combines Feature Congestion (FC), Edge Density (ED), and Subband Entropy (SE)
using the weights proposed by Rosenholtz et al. and converts the result to a
0-100 readability score (higher = better / less clutter).
"""

from __future__ import annotations


def compute_clutter_score(fc: float, ed: float, se: float) -> dict:
    """
    Compute a composite cognitive-load score from three normalised metrics.

    Weights (Rosenholtz et al.)
    ---------------------------
    * Feature Congestion  — 0.40
    * Edge Density        — 0.30
    * Subband Entropy     — 0.30

    All inputs must be in **[0, 1]** (higher = more clutter).

    The raw weighted sum is inverted and scaled so that the output score is
    in **[0, 100]** where:

    * **80 – 100**  → ``"low"``      cognitive load (clean design)
    * **55 – 79**   → ``"moderate"`` cognitive load
    * **0  – 54**   → ``"high"``     cognitive load (cluttered design)

    Parameters
    ----------
    fc:
        Feature-congestion score in [0, 1].
    ed:
        Edge-density score in [0, 1].
    se:
        Subband-entropy score in [0, 1].

    Returns
    -------
    dict
        Keys: ``cognitive_load_score``, ``severity``, ``raw_metrics``,
        ``weights_used``, ``recommendations``.
    """
    # Weighted clutter index (0 = perfectly clean, 1 = maximum clutter)
    raw: float = 0.40 * fc + 0.30 * ed + 0.30 * se

    # Invert and scale to [0, 100] readability score
    score: float = max(0.0, min(100.0, (1.0 - raw) * 100.0))

    # Severity band
    if score >= 80.0:
        severity = "low"
    elif score >= 55.0:
        severity = "moderate"
    else:
        severity = "high"

    # Targeted recommendations
    recommendations: list[str] = []

    if fc > 0.5:
        recommendations.append(
            "Reduce color variety and contrast variation in dense UI regions."
        )
    if ed > 0.3:
        recommendations.append(
            "Simplify layout by reducing borders, dividers, and decorative elements."
        )
    if se > 0.5:
        recommendations.append(
            "Increase whitespace and group related elements to reduce information entropy."
        )

    if not recommendations:
        recommendations.append(
            "Visual complexity is within acceptable bounds. No major changes needed."
        )

    return {
        "cognitive_load_score": round(score, 2),
        "severity": severity,
        "raw_metrics": {
            "feature_congestion": round(fc, 4),
            "edge_density": round(ed, 4),
            "subband_entropy": round(se, 4),
        },
        "weights_used": {
            "feature_congestion": 0.40,
            "edge_density": 0.30,
            "subband_entropy": 0.30,
        },
        "recommendations": recommendations,
    }
