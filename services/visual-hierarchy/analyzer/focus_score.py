"""
analyzer/focus_score.py
-----------------------
Focus Efficiency Score (FES) — measures how well CTA regions align with
high-attention areas of a UI screenshot.

Formula
-------
    FES(cta_i) = mean_saliency(cta_i bbox) / mean_saliency(global image) × 100

    FES > 100  → CTA lives in a high-attention zone (favourable)
    FES < 100  → CTA is buried in a low-attention region (needs improvement)

    overall_FES = mean(FES for all CTAs) / 2   (normalised to [0, 100])

Public API
----------
compute_focus_efficiency(saliency_map, cta_regions) → dict
compute_recommendations(focus_data) → list[str]
"""

import logging

import numpy as np

logger = logging.getLogger(__name__)


def compute_focus_efficiency(
    saliency_map: np.ndarray,
    cta_regions: list[dict],
) -> dict:
    """
    Compute the Focus Efficiency Score for all detected CTA regions.

    Parameters
    ----------
    saliency_map : np.ndarray
        Float32 saliency values in [0, 1], shape (H, W).
    cta_regions : list[dict]
        Output of cta_detector.detect_cta_regions().
        Each dict must contain 'x', 'y', 'w', 'h' keys.

    Returns
    -------
    dict with keys:
        focus_efficiency_score : float   Overall FES normalised to [0, 100].
        cta_analysis           : list    Per-CTA breakdown.
        global_mean_saliency   : float   Mean saliency of the full image.
        interpretation         : str     Human-readable quality label.
    """
    global_mean = float(saliency_map.mean())
    h, w = saliency_map.shape

    # ── No CTAs or degenerate saliency map ──────────────────────────────────
    if not cta_regions or global_mean < 1e-8:
        return {
            "focus_efficiency_score": 50.0,
            "cta_analysis": [],
            "global_mean_saliency": round(global_mean, 4),
            "interpretation": "No CTA regions detected. Score set to neutral.",
        }

    # ── Per-CTA analysis ─────────────────────────────────────────────────────
    cta_analysis: list[dict] = []
    for i, cta in enumerate(cta_regions):
        x, y, bw, bh = cta["x"], cta["y"], cta["w"], cta["h"]

        # Clamp bounding box to image dimensions
        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(w, x + bw), min(h, y + bh)

        if x2 <= x1 or y2 <= y1:
            logger.debug("CTA %d bounding box outside image bounds; skipping.", i)
            continue

        region_sal = saliency_map[y1:y2, x1:x2]
        region_mean = float(region_sal.mean())
        fes = (region_mean / global_mean) * 100.0
        status = "well-placed" if fes >= 100.0 else "needs-improvement"

        cta_analysis.append(
            {
                "cta_index": i,
                "region": {k: cta[k] for k in ("x", "y", "w", "h")},
                "region_mean_saliency": round(region_mean, 4),
                "fes": round(fes, 2),
                "status": status,
            }
        )

    # ── Aggregate ─────────────────────────────────────────────────────────────
    if not cta_analysis:
        overall_fes = 50.0
    else:
        raw_fes = float(np.mean([c["fes"] for c in cta_analysis]))
        # Normalise: raw FES 200 → score 100, raw FES 100 → score 50, raw FES 0 → score 0
        overall_fes = min(100.0, raw_fes / 2.0)

    # ── Interpretation label ──────────────────────────────────────────────────
    if overall_fes >= 75.0:
        interpretation = "Excellent — CTAs are positioned in high-attention zones."
    elif overall_fes >= 50.0:
        interpretation = "Good — Most CTAs are in reasonably visible areas."
    else:
        interpretation = (
            "Poor — Key CTAs are buried in low-attention regions. "
            "Consider repositioning."
        )

    return {
        "focus_efficiency_score": round(overall_fes, 2),
        "cta_analysis": cta_analysis,
        "global_mean_saliency": round(global_mean, 4),
        "interpretation": interpretation,
    }


def compute_recommendations(focus_data: dict) -> list[str]:
    """
    Generate human-readable UX improvement recommendations from FES output.

    Parameters
    ----------
    focus_data : dict
        The return value of compute_focus_efficiency().

    Returns
    -------
    list[str]
        Ordered list of actionable recommendation strings.
        Returns a single positive statement when no issues are found.
    """
    recs: list[str] = []
    score = focus_data.get("focus_efficiency_score", 50.0)

    if score < 50.0:
        recs.append(
            "Move primary CTA buttons toward the top-center of the viewport "
            "where attention naturally flows."
        )
        recs.append(
            "Increase the contrast and size of CTA buttons to attract more "
            "visual attention relative to surrounding elements."
        )

    for cta in focus_data.get("cta_analysis", []):
        if cta["status"] == "needs-improvement":
            rx, ry = cta["region"]["x"], cta["region"]["y"]
            recs.append(
                f"CTA at ({rx}, {ry}) has low visibility "
                f"(FES={cta['fes']}). "
                "Consider repositioning it, increasing its size, or adding "
                "a stronger colour accent to draw the user's eye."
            )

    if not recs:
        recs.append(
            "Visual hierarchy is effective. "
            "CTAs are well-positioned in high-attention zones."
        )

    return recs
