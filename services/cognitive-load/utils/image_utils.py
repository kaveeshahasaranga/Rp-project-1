"""
Image utility helpers for the cognitive-load microservice.

Provides base64 decoding, image-dimension querying, and temp-file cleanup.
"""

from __future__ import annotations

import base64
import logging
import os
import re

from PIL import Image

logger = logging.getLogger(__name__)

# Matches "data:<mime>;base64," prefixes produced by browsers / data URIs.
_DATA_URI_RE = re.compile(r"^data:[^;]+;base64,", re.IGNORECASE)


def decode_base64_image(b64_string: str, output_path: str) -> str:
    """
    Decode a base64-encoded image and write it to *output_path*.

    Strips any ``data:<mime>;base64,`` prefix before decoding so that both
    raw base64 strings and browser data-URI strings are accepted.

    Parameters
    ----------
    b64_string:
        The base64-encoded image data (with or without a data-URI prefix).
    output_path:
        Absolute path where the decoded binary should be written.

    Returns
    -------
    str
        The *output_path* that was written to.

    Raises
    ------
    ValueError
        If *b64_string* is empty or cannot be decoded.
    OSError
        If the file cannot be written to *output_path*.
    """
    if not b64_string:
        raise ValueError("b64_string must not be empty.")

    # Strip data-URI prefix
    clean = _DATA_URI_RE.sub("", b64_string).strip()

    try:
        raw_bytes = base64.b64decode(clean, validate=False)
    except Exception as exc:
        raise ValueError(f"Failed to decode base64 string: {exc}") from exc

    if not raw_bytes:
        raise ValueError("Decoded image data is empty.")

    with open(output_path, "wb") as fh:
        fh.write(raw_bytes)

    logger.debug("Wrote %d bytes to %s", len(raw_bytes), output_path)
    return output_path


def get_image_dimensions(image_path: str) -> tuple[int, int]:
    """
    Return the (width, height) of the image at *image_path* in pixels.

    Parameters
    ----------
    image_path:
        Absolute path to a valid image file supported by Pillow.

    Returns
    -------
    tuple[int, int]
        ``(width, height)`` in pixels.

    Raises
    ------
    FileNotFoundError
        If *image_path* does not exist.
    OSError
        If Pillow cannot open the file.
    """
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Image not found: {image_path!r}")

    with Image.open(image_path) as img:
        width, height = img.size

    logger.debug("Image dimensions for %s: %dx%d", image_path, width, height)
    return width, height


def cleanup_temp(path: str) -> None:
    """
    Remove a file at *path* if it exists; silently ignore missing files.

    Parameters
    ----------
    path:
        Absolute path to the temporary file to remove.
    """
    try:
        if path and os.path.isfile(path):
            os.remove(path)
            logger.debug("Removed temp file: %s", path)
    except OSError as exc:
        logger.warning("Could not remove temp file %s: %s", path, exc)
