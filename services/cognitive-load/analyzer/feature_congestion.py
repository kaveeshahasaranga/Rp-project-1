"""
Feature Congestion metric for cognitive-load analysis.

PRIMARY path:  Uses the `visual_clutter` library (Rosenholtz et al. 2007).
FALLBACK path: LAB-space patch standard-deviation approximation via OpenCV.

Both paths return a float in [0, 1] where 1 = maximum clutter.
"""

import logging
import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Attempt to import the optional visual_clutter library once at module load.
# ---------------------------------------------------------------------------
try:
    from visual_clutter import Vlc as _Vlc  # type: ignore
    _VLC_AVAILABLE = True
    logger.info("visual_clutter library loaded — using primary FC implementation.")
except ImportError:
    _VLC_AVAILABLE = False
    logger.warning(
        "visual_clutter not available — falling back to OpenCV LAB-patch approximation."
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_feature_congestion(image_path: str) -> float:
    """
    Compute the Feature Congestion clutter score for the given image.

    Attempts to use the Rosenholtz ``visual_clutter`` library first.
    If unavailable, falls back to a LAB-space patch variance approximation.

    Parameters
    ----------
    image_path:
        Absolute path to the image file.

    Returns
    -------
    float
        Normalised clutter score in the range [0, 1].
        0 = clean / no clutter.  1 = maximum clutter.
    """
    if _VLC_AVAILABLE:
        return _fc_primary(image_path)
    return _fc_fallback(image_path)


# ---------------------------------------------------------------------------
# Primary implementation — visual_clutter library
# ---------------------------------------------------------------------------

def _fc_primary(image_path: str) -> float:
    """
    Use ``visual_clutter.Vlc.getClutter_FC`` to compute Feature Congestion.

    Typical FC values from Rosenholtz et al. range from 0 to ~100.
    We normalise by dividing by 100 and clamping to [0, 1].
    """
    try:
        from visual_clutter import Vlc  # type: ignore  # noqa: F401 (already imported above, but keep local for clarity)

        vlc = Vlc(image_path)
        scalar, _clutter_map = vlc.getClutter_FC(p=1, pix=1)
        normalised = float(scalar) / 100.0
        return max(0.0, min(1.0, normalised))

    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("Primary FC computation failed (%s); switching to fallback.", exc)
        return _fc_fallback(image_path)


# ---------------------------------------------------------------------------
# Fallback implementation — OpenCV LAB-space patch variance
# ---------------------------------------------------------------------------

def _fc_fallback(image_path: str) -> float:
    """
    Approximate Feature Congestion via per-patch LAB standard deviations.

    Algorithm
    ---------
    1. Read the image and convert to CIE-LAB colour space.
    2. Divide into non-overlapping 16 × 16 pixel patches.
    3. For every patch, compute the std-dev of the L, A, and B channels.
    4. Return the mean across all patch–channel std-devs, normalised to [0, 1].
       L ∈ [0, 100], A & B ∈ [-127, 128] in OpenCV's uint8 encoding [0, 255].
       We normalise raw mean by 60 (empirically reasonable upper bound) and clamp.
    """
    import cv2  # local import — may not be installed on test machines

    try:
        img_bgr = cv2.imread(image_path)
        if img_bgr is None:
            raise ValueError(f"cv2.imread returned None for path: {image_path!r}")

        img_lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)

        patch_size = 16
        h, w, _ = img_lab.shape
        stds: list[float] = []

        for row in range(0, h - patch_size + 1, patch_size):
            for col in range(0, w - patch_size + 1, patch_size):
                patch = img_lab[row: row + patch_size, col: col + patch_size, :]
                for ch in range(3):
                    stds.append(float(np.std(patch[:, :, ch])))

        if not stds:
            # Image smaller than one patch — compute global std
            for ch in range(3):
                stds.append(float(np.std(img_lab[:, :, ch])))

        mean_std = float(np.mean(stds))
        # Normalise: std of a uniform [0,255] channel ≈ 73.6; use 60 as practical ceiling.
        normalised = mean_std / 60.0
        return max(0.0, min(1.0, normalised))

    except Exception as exc:  # pylint: disable=broad-except
        logger.error("FC fallback computation failed: %s", exc)
        return 0.0
