"""
Subband Entropy metric for cognitive-load analysis.

Uses a 3-level Haar Discrete Wavelet Transform (DWT) to decompose the
image into frequency subbands.  The Shannon entropy of each detail subband
captures the local information complexity.  Higher entropy → more clutter.
"""

import logging

import cv2
import numpy as np
import pywt
from scipy.stats import entropy as scipy_entropy

logger = logging.getLogger(__name__)

# Maximum theoretical entropy for an 8-bit channel (log2(256) ≈ 8.0 bits).
_MAX_ENTROPY: float = np.log2(256)  # ≈ 8.0


def compute_subband_entropy(image_path: str) -> float:
    """
    Compute the mean Haar wavelet subband entropy of the image.

    Algorithm
    ---------
    1. Read the image as grayscale float32 in [0, 1].
    2. Apply a 3-level 2-D Haar DWT via ``pywt.wavedec2``.
    3. For every *detail* subband (LH, HL, HH) at each level, compute the
       Shannon entropy of the absolute coefficient values
       (``scipy.stats.entropy`` with base-2 logarithm).
    4. Return the mean of all 9 subband entropies, normalised by
       ``log2(256) ≈ 8.0`` so that the result lies in [0, 1].

    Parameters
    ----------
    image_path:
        Absolute path to the image file.

    Returns
    -------
    float
        Normalised mean subband entropy in [0, 1].
        0 = completely flat / no information.  1 = maximum information density.

    Raises
    ------
    ValueError
        If the image cannot be read from *image_path*.
    """
    try:
        img_bgr = cv2.imread(image_path)
        if img_bgr is None:
            raise ValueError(f"cv2.imread returned None for path: {image_path!r}")

        # Convert to float32 grayscale in [0, 1]
        img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0

        # 3-level 2-D Haar DWT
        # coeffs = [cA3, (cH3, cV3, cD3), (cH2, cV2, cD2), (cH1, cV1, cD1)]
        coeffs = pywt.wavedec2(img_gray, wavelet="haar", level=3)

        entropies: list[float] = []
        # Skip coeffs[0] (approximation subband), iterate over detail levels
        for level_detail in coeffs[1:]:
            for subband in level_detail:  # LH, HL, HH
                flat = np.abs(subband.flatten()) + 1e-10
                h = float(scipy_entropy(flat, base=2))
                entropies.append(h)

        if not entropies:
            logger.warning("No detail subbands found; returning 0.")
            return 0.0

        mean_entropy = float(np.mean(entropies))
        normalised = mean_entropy / _MAX_ENTROPY
        result = max(0.0, min(1.0, normalised))

        logger.debug("Subband entropy for %s: raw=%.4f  normalised=%.4f",
                     image_path, mean_entropy, result)
        return result

    except ValueError:
        raise
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Subband entropy computation failed for %s: %s", image_path, exc)
        return 0.0
