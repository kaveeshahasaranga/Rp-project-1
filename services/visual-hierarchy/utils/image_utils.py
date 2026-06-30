"""
utils/image_utils.py
--------------------
Shared image loading and manipulation helpers for the visual-hierarchy service.

Public API
----------
decode_base64_image(b64_string)              → np.ndarray (BGR)
get_image_dimensions(image_np)               → dict {'width', 'height', 'channels'}
cleanup_temp(path)                           → None
load_image_bgr(path)                         → np.ndarray (BGR)
resize_for_display(img, max_dim)             → np.ndarray (BGR)
"""

import base64
import logging
import os
from io import BytesIO

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Base64 decoding
# ---------------------------------------------------------------------------

def decode_base64_image(b64_string: str) -> np.ndarray:
    """
    Decode a base64-encoded image string into a BGR numpy array.

    Accepts both plain base64 and data-URI format
    (e.g. ``data:image/png;base64,<data>``).

    Parameters
    ----------
    b64_string : str
        Base64-encoded image data, optionally with a data-URI prefix.

    Returns
    -------
    np.ndarray
        Decoded image in BGR uint8 format, shape (H, W, 3).

    Raises
    ------
    ValueError
        If decoding or conversion fails.
    """
    try:
        # Strip data-URI prefix if present
        if "," in b64_string:
            b64_string = b64_string.split(",", 1)[1]

        img_bytes = base64.b64decode(b64_string)
        pil_img = Image.open(BytesIO(img_bytes)).convert("RGB")
        img_np = np.array(pil_img, dtype=np.uint8)
        # PIL gives RGB; convert to BGR for OpenCV consistency
        bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        return bgr
    except Exception as exc:
        raise ValueError(f"Failed to decode base64 image: {exc}") from exc


# ---------------------------------------------------------------------------
# Dimension query
# ---------------------------------------------------------------------------

def get_image_dimensions(image_np: np.ndarray) -> dict:
    """
    Return the spatial dimensions and channel count of an image array.

    Parameters
    ----------
    image_np : np.ndarray
        Image array with shape (H, W) or (H, W, C).

    Returns
    -------
    dict
        ``{'width': int, 'height': int, 'channels': int}``
    """
    if image_np.ndim == 2:
        h, w = image_np.shape
        channels = 1
    else:
        h, w = image_np.shape[:2]
        channels = image_np.shape[2]
    return {"width": w, "height": h, "channels": channels}


# ---------------------------------------------------------------------------
# Temp file cleanup
# ---------------------------------------------------------------------------

def cleanup_temp(path: str) -> None:
    """
    Safely remove a temporary file, silently ignoring missing-file errors.

    Parameters
    ----------
    path : str
        Absolute or relative path to the file to delete.
    """
    try:
        if path and os.path.exists(path):
            os.remove(path)
            logger.debug("Removed temp file: %s", path)
    except OSError as exc:
        logger.warning("Could not remove temp file %s: %s", path, exc)


# ---------------------------------------------------------------------------
# Disk loading
# ---------------------------------------------------------------------------

def load_image_bgr(path: str) -> np.ndarray:
    """
    Load an image from disk in BGR format using OpenCV.

    Parameters
    ----------
    path : str
        Path to the image file (supports JPEG, PNG, BMP, TIFF, WebP, …).

    Returns
    -------
    np.ndarray
        BGR uint8 image, shape (H, W, 3).

    Raises
    ------
    ValueError
        If the file does not exist or OpenCV cannot decode it.
    """
    if not os.path.exists(path):
        raise ValueError(f"Image file not found: {path}")

    img = cv2.imread(path)
    if img is None:
        raise ValueError(
            f"OpenCV could not decode image at '{path}'. "
            "Ensure the file is a supported image format."
        )
    return img


# ---------------------------------------------------------------------------
# Display resizing
# ---------------------------------------------------------------------------

def resize_for_display(img: np.ndarray, max_dim: int = 800) -> np.ndarray:
    """
    Resize an image so its largest dimension does not exceed *max_dim*,
    preserving the original aspect ratio.

    If the image is already smaller than *max_dim* in both dimensions,
    it is returned unchanged (no upscaling).

    Parameters
    ----------
    img : np.ndarray
        Input image, shape (H, W) or (H, W, C).
    max_dim : int
        Maximum allowed size for the longest edge (default 800 pixels).

    Returns
    -------
    np.ndarray
        Resized image, same dtype as input.
    """
    h, w = img.shape[:2]
    largest = max(h, w)
    if largest <= max_dim:
        return img  # already within bounds

    scale = max_dim / largest
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))
    return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
