"""
Geometry utility functions for the touch-target evaluator.

Provides pure-Python helpers for spatial calculations and element visibility
checks — no external dependencies required.
"""

from __future__ import annotations

import math


def euclidean_distance(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    """
    Compute the Euclidean distance between two 2-D points.

    Parameters
    ----------
    p1:
        First point as ``(x, y)``.
    p2:
        Second point as ``(x, y)``.

    Returns
    -------
    float
        The Euclidean distance ≥ 0.
    """
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return math.sqrt(dx * dx + dy * dy)


def centroid(x: float, y: float, w: float, h: float) -> tuple[float, float]:
    """
    Compute the centroid (centre point) of a bounding rectangle.

    Parameters
    ----------
    x:
        Left edge of the element (page-relative, CSS pixels).
    y:
        Top edge of the element (page-relative, CSS pixels).
    w:
        Width in CSS pixels.
    h:
        Height in CSS pixels.

    Returns
    -------
    tuple[float, float]
        ``(cx, cy)`` — the centre of the rectangle.
    """
    return (x + w / 2.0, y + h / 2.0)


def area(w: float, h: float) -> float:
    """
    Compute the area of a rectangle.

    Parameters
    ----------
    w:
        Width in CSS pixels.
    h:
        Height in CSS pixels.

    Returns
    -------
    float
        Area in square CSS pixels.  Returns 0 for non-positive dimensions.
    """
    if w <= 0 or h <= 0:
        return 0.0
    return float(w) * float(h)


def is_visible(el: dict) -> bool:
    """
    Determine whether an element dict represents a visible DOM element.

    An element is considered **not** visible if any of the following CSS
    properties indicate hidden state:
    * ``display``    == ``"none"``
    * ``visibility`` == ``"hidden"``
    * ``opacity``    == ``"0"`` (or numeric 0)

    Zero-area elements (width or height ≤ 0) are also treated as not visible.

    Parameters
    ----------
    el:
        Element descriptor dict.  Expected keys: ``display``, ``visibility``,
        ``opacity``, ``width``, ``height``.

    Returns
    -------
    bool
        ``True`` if the element appears visible to the user.
    """
    if str(el.get("display", "")).lower() == "none":
        return False
    if str(el.get("visibility", "")).lower() == "hidden":
        return False
    opacity_raw = str(el.get("opacity", "1")).strip()
    try:
        if float(opacity_raw) == 0.0:
            return False
    except ValueError:
        pass  # non-numeric opacity string — treat as visible
    if int(el.get("width", 1)) <= 0 or int(el.get("height", 1)) <= 0:
        return False
    return True
