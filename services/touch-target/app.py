"""
Touch Target Evaluator — Flask microservice (port 8002).

Accepts a URL, extracts all interactive DOM elements via Playwright, then
evaluates them against WCAG touch-target guidelines (2.5.5 / 2.5.8),
Fitts's Law index of difficulty, and accidental-click risk via DBSCAN
clustering.
"""

import logging
import re

from flask import Flask, jsonify, request
from flask_cors import CORS

from analyzer.dom_extractor import extract_elements
from analyzer.wcag_checker import check_element, compute_compliance_stats
from analyzer.fitts_law import analyze_fitts_compliance
from analyzer.clustering import detect_accidental_click_clusters
from utils.geometry_utils import is_visible

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger("touch-target")

app = Flask(__name__)
CORS(app)

_URL_RE = re.compile(
    r"^https?://"               # scheme
    r"(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,}"  # domain
    r"(?::\d+)?(?:/[^\s]*)?$",  # optional port + path
    re.IGNORECASE,
)


def _validate_url(url: str) -> str | None:
    """
    Return an error string if *url* is invalid, otherwise None.

    Only http and https schemes are accepted.
    """
    if not url:
        return "Field 'url' is required and must not be empty."
    if not _URL_RE.match(url.strip()):
        return (
            f"Invalid URL: {url!r}. "
            "Must be a fully-qualified http(s) URL, e.g. https://example.com"
        )
    return None


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    """Return service health status."""
    return jsonify({"status": "ok", "service": "touch-target"}), 200


# ---------------------------------------------------------------------------
# Main analysis endpoint
# ---------------------------------------------------------------------------

@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Evaluate all interactive touch targets on the given URL.

    Request JSON schema:
        { "url": "https://example.com" }

    Response JSON schema:
        {
            "url": "...",
            "total_elements_found": N,
            "visible_elements_analyzed": M,
            "wcag_compliance": { ... },
            "fitts_law": { ... },
            "clustering": { ... },
            "elements": [ { ... }, ... ]
        }
    """
    try:
        payload = request.get_json(force=True, silent=True)
        if not payload:
            return jsonify({"error": "Request body must be valid JSON."}), 400

        url = (payload.get("url") or "").strip()
        err = _validate_url(url)
        if err:
            return jsonify({"error": err}), 422

        # ------------------------------------------------------------------
        # 1. Extract interactive DOM elements via headless Playwright
        # ------------------------------------------------------------------
        logger.info("Extracting elements from %s", url)
        raw_elements = extract_elements(url)
        logger.info("Found %d raw elements", len(raw_elements))

        # ------------------------------------------------------------------
        # 2. Filter to visible elements only
        # ------------------------------------------------------------------
        visible = [el for el in raw_elements if is_visible(el)]
        logger.info("%d visible elements after filtering", len(visible))

        # ------------------------------------------------------------------
        # 3. WCAG compliance checks
        # ------------------------------------------------------------------
        checked = [check_element(el) for el in visible]
        wcag_stats = compute_compliance_stats(checked)

        # ------------------------------------------------------------------
        # 4. Fitts's Law analysis
        # ------------------------------------------------------------------
        fitts_result = analyze_fitts_compliance(checked)

        # ------------------------------------------------------------------
        # 5. DBSCAN accidental-click risk clustering
        # ------------------------------------------------------------------
        cluster_result = detect_accidental_click_clusters(checked)

        return jsonify({
            "url": url,
            "total_elements_found": len(raw_elements),
            "visible_elements_analyzed": len(visible),
            "wcag_compliance": wcag_stats,
            "fitts_law": fitts_result,
            "clustering": cluster_result,
            "elements": checked,
        }), 200

    except TimeoutError as exc:
        logger.warning("Page load timed out for %s: %s", url if "url" in dir() else "?", exc)
        return jsonify({"error": f"Page timed out: {exc}"}), 504

    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Unexpected error during touch-target analysis")
        return jsonify({"error": f"Internal server error: {exc}"}), 500


# ---------------------------------------------------------------------------
# Entry point (development server only — production uses gunicorn)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8002, debug=False)
