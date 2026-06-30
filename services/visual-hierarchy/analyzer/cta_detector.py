"""
analyzer/cta_detector.py
------------------------
Heuristic CTA (Call-To-Action) region detector for UI screenshots.

Detection strategy
------------------
1. Convert image to HSV colour space.
2. Threshold for high-saturation, medium-to-high value pixels
   (typical of colourful button elements).
3. Morphologically close the mask to merge nearby pixels into solid blobs.
4. Extract external contours and filter by:
   - Minimum area  : 800 px²  (eliminates icons / tiny decorations)
   - Maximum area  : 60 % of image area  (eliminates full-width banners)
   - Aspect ratio  : 1.5 – 10  (wider-than-tall, button-like shape)
5. Return up to 5 candidate regions sorted by area (largest first).

Public API
----------
detect_cta_regions(image_bgr) → list[dict]
    Each dict: {'x', 'y', 'w', 'h', 'confidence'}
"""

import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def detect_cta_regions(image_bgr: np.ndarray) -> list[dict]:
    """
    Detect probable CTA (button) regions in a UI screenshot via colour heuristics.

    Parameters
    ----------
    image_bgr : np.ndarray
        Input screenshot in BGR uint8 format, shape (H, W, 3).

    Returns
    -------
    list[dict]
        Up to 5 candidate CTA bounding boxes, each containing:
          x, y       – top-left corner (pixels)
          w, h       – width and height (pixels)
          confidence – fill ratio of the contour within its bounding box [0, 1]
        Sorted descending by bounding-box area.
    """
    if image_bgr is None or image_bgr.ndim != 3:
        logger.warning("detect_cta_regions: invalid input image.")
        return []

    h, w = image_bgr.shape[:2]
    image_area = h * w

    # ── Colour mask: high saturation, medium-high value ──────────────────────
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    lower = np.array([0, 80, 80], dtype=np.uint8)
    upper = np.array([180, 255, 255], dtype=np.uint8)
    mask = cv2.inRange(hsv, lower, upper)

    # ── Morphological closing: fills gaps inside button blobs ─────────────────
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # ── Contour extraction ───────────────────────────────────────────────────
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    ctas: list[dict] = []
    for cnt in contours:
        x, y, bw, bh = cv2.boundingRect(cnt)
        bbox_area = bw * bh

        # Size filter
        if bbox_area < 800:
            continue
        if bbox_area > 0.6 * image_area:
            continue

        # Aspect ratio filter (button-like: wider than tall)
        aspect = bw / max(bh, 1)
        if aspect < 1.5 or aspect > 10.0:
            continue

        # Confidence = how densely the contour fills its own bounding box
        cnt_area = float(cv2.contourArea(cnt))
        confidence = round(cnt_area / max(bbox_area, 1), 3)

        ctas.append(
            {
                "x": int(x),
                "y": int(y),
                "w": int(bw),
                "h": int(bh),
                "confidence": confidence,
            }
        )

    # ── Sort by bounding-box area descending (most prominent CTA first) ───────
    ctas.sort(key=lambda c: c["w"] * c["h"], reverse=True)
    logger.debug("detect_cta_regions: found %d candidate(s).", len(ctas[:5]))
    return ctas[:5]
