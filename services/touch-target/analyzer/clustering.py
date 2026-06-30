"""
DBSCAN-based accidental-click risk detector for touch targets.

Groups interactive elements whose centroids are within 35 CSS pixels of each
other into spatial clusters.  Dense clusters indicate that multiple tap targets
are packed so close together that users are likely to activate the wrong one.

Algorithm
---------
1. Compute (cx, cy) centroid for each element.
2. Run DBSCAN(eps=35, min_samples=3) on the 2-D centroid array.
3. Label each cluster; noise points (label = -1) are excluded.
4. Derive a risk level from the number and size of clusters found.

Risk levels
-----------
* ``low``      — 0 clusters detected
* ``moderate`` — 1–2 clusters detected
* ``high``     — 3 or more clusters detected
"""

from __future__ import annotations

import logging

import numpy as np
from sklearn.cluster import DBSCAN

from utils.geometry_utils import centroid

logger = logging.getLogger(__name__)

# DBSCAN hyperparameters (CSS pixels)
DBSCAN_EPS: float = 35.0
DBSCAN_MIN_SAMPLES: int = 3


def detect_accidental_click_clusters(elements: list[dict]) -> dict:
    """
    Detect clusters of tightly-packed interactive elements.

    Parameters
    ----------
    elements:
        List of element dicts with at least ``x``, ``y``, ``width``,
        ``height`` fields (integers / floats).

    Returns
    -------
    dict
        Keys:
        * ``n_clusters``                 — int
        * ``accidental_click_clusters``  — list of cluster descriptors
            Each descriptor: { "cluster_id": int, "element_count": int,
                               "centroid": [cx, cy] }
        * ``risk_level``                 — "low" | "moderate" | "high"
        * ``parameters``                 — DBSCAN params used
    """
    # Build centroid matrix
    points: list[tuple[float, float]] = []
    valid_elements: list[dict] = []

    for el in elements:
        w = float(el.get("width", 0))
        h = float(el.get("height", 0))
        x = float(el.get("x", 0))
        y = float(el.get("y", 0))
        if w > 0 and h > 0:
            cx, cy = centroid(x, y, w, h)
            points.append((cx, cy))
            valid_elements.append(el)

    if not points:
        return {
            "n_clusters": 0,
            "accidental_click_clusters": [],
            "risk_level": "low",
            "parameters": {"eps": DBSCAN_EPS, "min_samples": DBSCAN_MIN_SAMPLES},
        }

    X = np.array(points, dtype=np.float64)
    labels = DBSCAN(eps=DBSCAN_EPS, min_samples=DBSCAN_MIN_SAMPLES).fit_predict(X)

    # Collect cluster summaries (exclude noise label -1)
    unique_labels = sorted(set(labels) - {-1})
    cluster_summaries: list[dict] = []
    for label in unique_labels:
        mask = labels == label
        cluster_pts = X[mask]
        cx_mean, cy_mean = float(cluster_pts[:, 0].mean()), float(cluster_pts[:, 1].mean())
        cluster_summaries.append({
            "cluster_id": int(label),
            "element_count": int(mask.sum()),
            "centroid": [round(cx_mean, 1), round(cy_mean, 1)],
        })

    n_clusters = len(cluster_summaries)

    if n_clusters == 0:
        risk_level = "low"
    elif n_clusters <= 2:
        risk_level = "moderate"
    else:
        risk_level = "high"

    logger.info(
        "DBSCAN clustering: %d clusters → risk_level=%s", n_clusters, risk_level
    )

    return {
        "n_clusters": n_clusters,
        "accidental_click_clusters": cluster_summaries,
        "risk_level": risk_level,
        "parameters": {"eps": DBSCAN_EPS, "min_samples": DBSCAN_MIN_SAMPLES},
    }
