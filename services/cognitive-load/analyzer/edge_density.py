"""
Edge Density metric for cognitive-load analysis.

Uses the Canny edge detector to measure the proportion of edge pixels
in a screenshot.  A higher ratio indicates a more complex, cluttered UI.
"""

import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def compute_edge_density(image_path: str) -> float:
    """
    Canny-based edge density.

    Converts the image to grayscale, applies a Gaussian blur to reduce noise,
    then runs Canny edge detection.  Returns the ratio of edge pixels to the
    total number of pixels — a value in [0, 1].

    Parameters
    ----------
    image_path:
        Absolute path to the image file.

    Returns
    -------
    float
        Edge-pixel ratio in [0, 1].  0 = no edges, 1 = all pixels are edges.

    Raises
    ------
    ValueError
        If the image cannot be read from *image_path*.
    """
    try:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError(f"cv2.imread returned None for path: {image_path!r}")

        blurred = cv2.GaussianBlur(img, (5, 5), 1.4)
        edges = cv2.Canny(blurred, threshold1=50, threshold2=150)

        density = float(np.count_nonzero(edges)) / float(edges.size)
        logger.debug("Edge density for %s: %.4f", image_path, density)
        return density

    except ValueError:
        raise
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Edge density computation failed for %s: %s", image_path, exc)
        return 0.0
