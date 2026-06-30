"""
Cognitive Load Analyzer — Flask microservice (port 8001).

Analyzes UI screenshots for visual complexity using three complementary
metrics: Feature Congestion, Edge Density, and Subband Entropy.
"""

import logging
import os
import tempfile
import uuid

from flask import Flask, jsonify, request
from flask_cors import CORS

from analyzer.feature_congestion import compute_feature_congestion
from analyzer.edge_density import compute_edge_density
from analyzer.subband_entropy import compute_subband_entropy
from analyzer.clutter_score import compute_clutter_score
from utils.image_utils import decode_base64_image, get_image_dimensions, cleanup_temp

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger("cognitive-load")

app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    """Return service health status."""
    return jsonify({"status": "ok", "service": "cognitive-load"}), 200


# ---------------------------------------------------------------------------
# Main analysis endpoint
# ---------------------------------------------------------------------------

@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Accept a base64-encoded screenshot and return a full cognitive load report.

    Request JSON schema:
        {
            "image_base64": "<base64 string or data-URI>",
            "filename":     "optional_name.png"   (default: "upload.png")
        }

    Returns a JSON object with cognitive_load_score, severity, raw_metrics,
    weights_used, recommendations, and image metadata.
    """
    tmp_path = None
    try:
        payload = request.get_json(force=True, silent=True)
        if not payload:
            return jsonify({"error": "Request body must be JSON."}), 400

        b64 = payload.get("image_base64", "").strip()
        if not b64:
            return jsonify({"error": "Field 'image_base64' is required and must not be empty."}), 400

        filename = payload.get("filename", "upload.png")
        ext = os.path.splitext(filename)[-1].lower() or ".png"

        # Write decoded image to a unique temp file
        tmp_path = os.path.join(tempfile.gettempdir(), f"cla_{uuid.uuid4().hex}{ext}")
        decode_base64_image(b64, tmp_path)
        logger.info("Saved temp image to %s", tmp_path)

        # Retrieve image dimensions for metadata
        width, height = get_image_dimensions(tmp_path)

        # ---- Run the three analyzers ----------------------------------------
        logger.info("Computing feature congestion…")
        fc = compute_feature_congestion(tmp_path)

        logger.info("Computing edge density…")
        ed = compute_edge_density(tmp_path)

        logger.info("Computing subband entropy…")
        se = compute_subband_entropy(tmp_path)

        logger.info("FC=%.4f  ED=%.4f  SE=%.4f", fc, ed, se)

        # ---- Compose the result ---------------------------------------------
        result = compute_clutter_score(fc, ed, se)
        result["image_metadata"] = {
            "filename": filename,
            "width_px": width,
            "height_px": height,
        }

        return jsonify(result), 200

    except ValueError as exc:
        logger.warning("Validation error: %s", exc)
        return jsonify({"error": str(exc)}), 422

    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Unexpected error during analysis")
        return jsonify({"error": f"Internal server error: {exc}"}), 500

    finally:
        if tmp_path:
            cleanup_temp(tmp_path)


# ---------------------------------------------------------------------------
# Entry point (development server only — production uses gunicorn)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001, debug=False)
