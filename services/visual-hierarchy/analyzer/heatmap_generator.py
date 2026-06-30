"""
analyzer/heatmap_generator.py
------------------------------
Generates visual saliency heatmap overlays and extracts top attention regions.

Public API
----------
generate_heatmap(original_bgr, saliency_map, alpha) → dict
    Keys: heatmap_base64 (PNG encoded), saliency_array (downsampled 2-D list), dimensions

get_top_attention_regions(saliency_map, n_regions) → list[dict]
    Returns top-N high-saliency rectangular bounding boxes.
"""

import base64
import logging
from io import BytesIO

import cv2
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

logger = logging.getLogger(__name__)


def generate_heatmap(
    original_bgr: np.ndarray,
    saliency_map: np.ndarray,
    alpha: float = 0.55,
) -> dict:
    """
    Overlay a JET colormap saliency heatmap on the original image.

    The saliency map is smoothed with a Gaussian filter before colorisation
    to remove high-frequency noise and produce a perceptually pleasing result.

    Parameters
    ----------
    original_bgr : np.ndarray
        Original image in BGR uint8 format, shape (H, W, 3).
    saliency_map : np.ndarray
        Float32 saliency values in [0, 1], shape (H, W).
    alpha : float
        Blending weight for the heatmap (0 = original only, 1 = heatmap only).
        Default 0.55 produces a clearly visible but non-obscuring overlay.

    Returns
    -------
    dict with keys:
        heatmap_base64 : str
            Base64-encoded PNG of the blended overlay image.
        saliency_array : list[list[float]]
            Downsampled 2-D saliency grid (≤100×100) suitable for JSON serialisation.
        dimensions : dict
            {'width': int, 'height': int} of the saliency map.
    """
    # ── Smooth ──────────────────────────────────────────────────────────────
    smoothed = gaussian_filter(saliency_map, sigma=12)
    s_min, s_max = smoothed.min(), smoothed.max()
    smoothed = (smoothed - s_min) / (s_max - s_min + 1e-8)

    # ── Colorise with JET ────────────────────────────────────────────────────
    sal_uint8 = (smoothed * 255).astype(np.uint8)
    heatmap_bgr = cv2.applyColorMap(sal_uint8, cv2.COLORMAP_JET)

    # ── Resize heatmap to match original if shapes differ ────────────────────
    orig_h, orig_w = original_bgr.shape[:2]
    if heatmap_bgr.shape[:2] != (orig_h, orig_w):
        heatmap_bgr = cv2.resize(heatmap_bgr, (orig_w, orig_h), interpolation=cv2.INTER_LINEAR)

    # ── Alpha-blend ──────────────────────────────────────────────────────────
    overlay_bgr = cv2.addWeighted(original_bgr, 1.0 - alpha, heatmap_bgr, alpha, 0)

    # ── Encode to base64 PNG ─────────────────────────────────────────────────
    overlay_rgb = cv2.cvtColor(overlay_bgr, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(overlay_rgb)
    buf = BytesIO()
    pil_img.save(buf, format="PNG", optimize=True)
    b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")

    # ── Downsample saliency array for JSON (max 100×100) ─────────────────────
    h, w = smoothed.shape
    step_h = max(1, h // 100)
    step_w = max(1, w // 100)
    saliency_array = smoothed[::step_h, ::step_w].tolist()

    return {
        "heatmap_base64": b64_str,
        "saliency_array": saliency_array,
        "dimensions": {"width": w, "height": h},
    }


def get_top_attention_regions(
    saliency_map: np.ndarray,
    n_regions: int = 5,
) -> list[dict]:
    """
    Identify the top-N highest-saliency rectangular regions using a sliding-window grid.

    The saliency map is first smoothed to reduce noise, then divided into a
    10×10 grid of overlapping blocks (50 % stride). Each block is scored by its
    mean saliency value and the top-N blocks are returned.

    Parameters
    ----------
    saliency_map : np.ndarray
        Float32 saliency values in [0, 1], shape (H, W).
    n_regions : int
        Number of regions to return (default 5).

    Returns
    -------
    list[dict]
        Each entry: {'x': int, 'y': int, 'w': int, 'h': int, 'mean_saliency': float}
        sorted descending by mean_saliency.
    """
    smoothed = gaussian_filter(saliency_map, sigma=15)
    h, w = smoothed.shape
    block_h = max(1, h // 10)
    block_w = max(1, w // 10)
    stride_h = max(1, block_h // 2)
    stride_w = max(1, block_w // 2)

    regions: list[dict] = []
    for ry in range(0, h - block_h + 1, stride_h):
        for rx in range(0, w - block_w + 1, stride_w):
            patch = smoothed[ry : ry + block_h, rx : rx + block_w]
            mean_sal = float(patch.mean())
            regions.append(
                {
                    "x": rx,
                    "y": ry,
                    "w": block_w,
                    "h": block_h,
                    "mean_saliency": round(mean_sal, 4),
                }
            )

    regions.sort(key=lambda r: r["mean_saliency"], reverse=True)
    return regions[:n_regions]
