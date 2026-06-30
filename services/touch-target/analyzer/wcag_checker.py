"""
WCAG touch-target compliance checker.

Evaluates interactive elements against three size thresholds:

* WCAG 2.5.8 AA  — 24 × 24 CSS pixels minimum
* WCAG 2.5.5 AAA — 44 × 44 CSS pixels minimum (enhanced)
* Material / iOS  — 48 × 48 CSS pixels recommended

References
----------
* https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html
* https://www.w3.org/WAI/WCAG22/Understanding/target-size-enhanced.html
* https://m3.material.io/foundations/accessible-design/accessibility-basics
"""

from __future__ import annotations

# WCAG threshold constants (CSS pixels)
WCAG_AA_MIN: int = 24        # WCAG 2.5.8, Level AA
WCAG_AAA_MIN: int = 44       # WCAG 2.5.5, Level AAA Enhanced
RECOMMENDED_MIN: int = 48    # Material Design / iOS HIG


def check_element(el: dict) -> dict:
    """
    Augment an element dict with WCAG touch-target compliance flags.

    Adds the following boolean fields to a shallow copy of *el*:
    * ``wcag_aa_pass``          — True if both width & height ≥ 24 px
    * ``wcag_aaa_pass``         — True if both width & height ≥ 44 px
    * ``recommended_pass``      — True if both width & height ≥ 48 px
    * ``issues``                — list of human-readable violation strings

    Parameters
    ----------
    el:
        Element descriptor dict (must have ``width``, ``height`` int fields).

    Returns
    -------
    dict
        A new dict containing all original fields plus the compliance fields.
    """
    w: int = int(el.get("width", 0))
    h: int = int(el.get("height", 0))

    aa_pass: bool = w >= WCAG_AA_MIN and h >= WCAG_AA_MIN
    aaa_pass: bool = w >= WCAG_AAA_MIN and h >= WCAG_AAA_MIN
    rec_pass: bool = w >= RECOMMENDED_MIN and h >= RECOMMENDED_MIN

    issues: list[str] = []
    if not aa_pass:
        issues.append(
            f"WCAG 2.5.8 AA violation: element is {w}×{h}px "
            f"(minimum {WCAG_AA_MIN}×{WCAG_AA_MIN}px required)."
        )
    if not aaa_pass:
        issues.append(
            f"WCAG 2.5.5 AAA violation: element is {w}×{h}px "
            f"(recommended {WCAG_AAA_MIN}×{WCAG_AAA_MIN}px for enhanced accessibility)."
        )
    if not rec_pass:
        issues.append(
            f"Below Material/iOS recommended minimum: {w}×{h}px "
            f"(recommended {RECOMMENDED_MIN}×{RECOMMENDED_MIN}px)."
        )

    return {
        **el,
        "wcag_aa_pass": aa_pass,
        "wcag_aaa_pass": aaa_pass,
        "recommended_pass": rec_pass,
        "issues": issues,
    }


def compute_compliance_stats(elements: list[dict]) -> dict:
    """
    Compute aggregate WCAG compliance statistics for a list of checked elements.

    Parameters
    ----------
    elements:
        List of element dicts that have already been processed by
        :func:`check_element` (must contain ``wcag_aa_pass``,
        ``wcag_aaa_pass``, ``recommended_pass`` keys).

    Returns
    -------
    dict
        Keys:
        * ``total_elements``            — int
        * ``wcag_aa_compliance_rate``   — float [0, 1]
        * ``wcag_aaa_compliance_rate``  — float [0, 1]
        * ``recommended_compliance_rate`` — float [0, 1]
        * ``violations``                — list of elements that fail AA
    """
    total: int = len(elements)
    if total == 0:
        return {
            "total_elements": 0,
            "wcag_aa_compliance_rate": 1.0,
            "wcag_aaa_compliance_rate": 1.0,
            "recommended_compliance_rate": 1.0,
            "violations": [],
        }

    aa_pass_count: int = sum(1 for el in elements if el.get("wcag_aa_pass"))
    aaa_pass_count: int = sum(1 for el in elements if el.get("wcag_aaa_pass"))
    rec_pass_count: int = sum(1 for el in elements if el.get("recommended_pass"))
    violations: list[dict] = [el for el in elements if not el.get("wcag_aa_pass")]

    return {
        "total_elements": total,
        "wcag_aa_compliance_rate": round(aa_pass_count / total, 4),
        "wcag_aaa_compliance_rate": round(aaa_pass_count / total, 4),
        "recommended_compliance_rate": round(rec_pass_count / total, 4),
        "violations": violations,
    }
