"""
app.py — Visual Hierarchy Predictor microservice
-------------------------------------------------
Port   : 8003
Author : ML-Driven UI/UX Heuristic Evaluation System

Endpoints
---------
POST /analyze        Accepts multipart/form-data ('image' file)
                     OR JSON body {'image_base64': '<b64 string>'}
                     Returns full saliency + heatmap + CTA + FES analysis.

GET  /health         Liveness check → {"status": "ok", "service": "visual-hierarchy"}
GET  /model-info     Reports active saliency model (TranSalNet-Res or SpectralResidual-CV)
"""

import io
import logging
import time

import cv2
import numpy as np
from flask import Flask, jsonify, request
from flask_cors import CORS
from PIL import Image

# ── Internal modules ──────────────────────────────────────────────────────────
from analyzer import cta_detector, focus_score, heatmap_generator, saliency_model
from utils.image_utils import decode_base64_image, get_image_dimensions

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes and origins

# ── Load saliency model at startup ────────────────────────────────────────────
with app.app_context():
    saliency_model.load_model()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _decode_request_image() -> np.ndarray:
    """
    Decode the request image from either multipart/form-data or JSON base64.

    Returns
    -------
    np.ndarray
        BGR uint8 image, shape (H, W, 3).

    Raises
    ------
    ValueError
        If no image is found or decoding fails.
    """
    # ── Multipart file upload ─────────────────────────────────────────────────
    if "image" in request.files:
        file = request.files["image"]
        file_bytes = file.read()
        if not file_bytes:
            raise ValueError("Uploaded file is empty.")
        img_array = np.frombuffer(file_bytes, dtype=np.uint8)
        bgr = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if bgr is None:
            raise ValueError("Could not decode uploaded image file.")
        return bgr

    # ── JSON base64 ───────────────────────────────────────────────────────────
    payload = request.get_json(silent=True) or {}
    b64 = payload.get("image_base64", "").strip()
    if not b64:
        raise ValueError(
            "No image provided. "
            "Send 'image' as multipart/form-data or "
            "{'image_base64': '...'} as JSON."
        )
    return decode_base64_image(b64)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health() -> tuple:
    """
    Liveness probe.

    Returns
    -------
    JSON
        ``{"status": "ok", "service": "visual-hierarchy"}``
    """
    return jsonify({"status": "ok", "service": "visual-hierarchy"}), 200


@app.route("/model-info", methods=["GET"])
def model_info() -> tuple:
    """
    Report which saliency model is currently active.

    Returns
    -------
    JSON
        ``{"active_model": "<name>", "device": "<cpu|cuda>"}``
    """
    import torch

    return jsonify(
        {
            "active_model": saliency_model.get_model_type(),
            "device": str(torch.device("cuda" if torch.cuda.is_available() else "cpu")),
            "description": (
                "TranSalNet-Res (deep learning, ResNet50 backbone)"
                if saliency_model.get_model_type() == "TranSalNet-Res"
                else "OpenCV Spectral Residual (CPU heuristic fallback)"
            ),
        }
    ), 200


@app.route("/analyze", methods=["POST"])
def analyze() -> tuple:
    """
    Run full visual hierarchy analysis on a UI screenshot.

    Accepts
    -------
    - ``multipart/form-data``  with field ``image`` (JPEG / PNG / WebP)
    - ``application/json``     with field ``image_base64`` (base64-encoded image)

    Returns
    -------
    JSON
        {
          "status": "success",
          "model_used": str,
          "image_dimensions": {"width": int, "height": int, "channels": int},
          "saliency": {
            "heatmap_base64":  str,           // PNG overlay, base64-encoded
            "saliency_array":  list[list],    // downsampled ≤100×100 grid
            "dimensions":      {"width", "height"},
            "top_attention_regions": list[dict]
          },
          "cta_regions": list[dict],
          "focus_efficiency": {
            "focus_efficiency_score": float,  // [0, 100]
            "cta_analysis":           list,
            "global_mean_saliency":   float,
            "interpretation":         str
          },
          "recommendations": list[str],
          "processing_time_ms": float
        }
    """
    t_start = time.perf_counter()

    # ── 1. Decode image ───────────────────────────────────────────────────────
    try:
        image_bgr = _decode_request_image()
    except ValueError as exc:
        logger.warning("Image decode error: %s", exc)
        return jsonify({"status": "error", "message": str(exc)}), 400
    except Exception as exc:
        logger.exception("Unexpected error decoding image.")
        return jsonify({"status": "error", "message": "Image decode failed."}), 500

    dimensions = get_image_dimensions(image_bgr)

    # ── 2. Saliency prediction ────────────────────────────────────────────────
    try:
        saliency_map = saliency_model.predict_saliency(image_bgr)
    except Exception as exc:
        logger.exception("Saliency prediction failed.")
        return (
            jsonify({"status": "error", "message": f"Saliency prediction error: {exc}"}),
            500,
        )

    # ── 3. Heatmap generation ─────────────────────────────────────────────────
    try:
        heatmap_data = heatmap_generator.generate_heatmap(image_bgr, saliency_map)
        top_regions = heatmap_generator.get_top_attention_regions(saliency_map)
        heatmap_data["top_attention_regions"] = top_regions
    except Exception as exc:
        logger.exception("Heatmap generation failed.")
        return (
            jsonify({"status": "error", "message": f"Heatmap generation error: {exc}"}),
            500,
        )

    # ── 4. CTA detection ──────────────────────────────────────────────────────
    try:
        cta_regions = cta_detector.detect_cta_regions(image_bgr)
    except Exception as exc:
        logger.exception("CTA detection failed.")
        return (
            jsonify({"status": "error", "message": f"CTA detection error: {exc}"}),
            500,
        )

    # ── 5. Focus Efficiency Score ─────────────────────────────────────────────
    try:
        focus_data = focus_score.compute_focus_efficiency(saliency_map, cta_regions)
        recommendations = focus_score.compute_recommendations(focus_data)
    except Exception as exc:
        logger.exception("Focus score computation failed.")
        return (
            jsonify({"status": "error", "message": f"Focus score error: {exc}"}),
            500,
        )

    # ── 6. Assemble response ──────────────────────────────────────────────────
    elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)
    logger.info(
        "Analysis complete — model=%s dims=%dx%d CTAs=%d FES=%.1f time=%.0fms",
        saliency_model.get_model_type(),
        dimensions["width"],
        dimensions["height"],
        len(cta_regions),
        focus_data["focus_efficiency_score"],
        elapsed_ms,
    )

    return (
        jsonify(
            {
                "status": "success",
                "model_used": saliency_model.get_model_type(),
                "image_dimensions": dimensions,
                "saliency": heatmap_data,
                "cta_regions": cta_regions,
                "focus_efficiency": focus_data,
                "recommendations": recommendations,
                "processing_time_ms": elapsed_ms,
            }
        ),
        200,
    )


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8003, debug=False)
