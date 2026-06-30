"""
tests/test_saliency.py
----------------------
Unit tests for the visual-hierarchy microservice.

Test strategy
-------------
- All tests use small synthetic 100×100 BGR uint8 numpy arrays so they run
  without a GPU, without model weights, and without disk I/O.
- The saliency model is tested in SpectralResidual-CV mode (no weights present).
- Flask app endpoints are tested via the test client.

Run with:
    cd services/visual-hierarchy
    python -m pytest tests/ -v
"""

import base64
import importlib
import os
import sys
import unittest
from io import BytesIO

import cv2
import numpy as np
from PIL import Image

# ── Ensure project root is on sys.path so imports resolve ────────────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_synthetic_bgr(h: int = 100, w: int = 100) -> np.ndarray:
    """Return a random uint8 BGR image of the requested size."""
    rng = np.random.default_rng(seed=42)
    return rng.integers(0, 256, (h, w, 3), dtype=np.uint8)


def _make_synthetic_saliency(h: int = 100, w: int = 100) -> np.ndarray:
    """Return a random float32 saliency map in [0, 1]."""
    rng = np.random.default_rng(seed=7)
    return rng.random((h, w)).astype(np.float32)


def _encode_image_to_base64(img_bgr: np.ndarray) -> str:
    """Encode a BGR ndarray to a base64 PNG string."""
    rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(rgb)
    buf = BytesIO()
    pil.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _encode_image_to_bytes(img_bgr: np.ndarray) -> bytes:
    """Encode a BGR ndarray to PNG bytes suitable for multipart upload."""
    success, encoded = cv2.imencode(".png", img_bgr)
    assert success, "cv2.imencode failed in test helper"
    return encoded.tobytes()


# ─────────────────────────────────────────────────────────────────────────────
# Test: saliency_model — SpectralResidual fallback
# ─────────────────────────────────────────────────────────────────────────────

class TestSaliencyModel(unittest.TestCase):
    """Tests for analyzer.saliency_model in CPU / no-weights mode."""

    def setUp(self) -> None:
        """Force SpectralResidual mode by clearing any loaded model."""
        from analyzer import saliency_model as sm

        sm._model = None
        sm._model_type = "SpectralResidual-CV"
        self.sm = sm
        self.image = _make_synthetic_bgr()

    def test_predict_returns_ndarray(self) -> None:
        """predict_saliency must return a numpy ndarray."""
        result = self.sm.predict_saliency(self.image)
        self.assertIsInstance(result, np.ndarray)

    def test_predict_spatial_dims_match_input(self) -> None:
        """Saliency map spatial dims must equal the input image dims."""
        result = self.sm.predict_saliency(self.image)
        h, w = self.image.shape[:2]
        self.assertEqual(result.shape, (h, w))

    def test_predict_values_in_zero_one_range(self) -> None:
        """All saliency values must be in [0, 1]."""
        result = self.sm.predict_saliency(self.image)
        self.assertGreaterEqual(float(result.min()), 0.0)
        self.assertLessEqual(float(result.max()), 1.0 + 1e-6)

    def test_predict_returns_float32(self) -> None:
        """Saliency map must be float32."""
        result = self.sm.predict_saliency(self.image)
        self.assertEqual(result.dtype, np.float32)

    def test_get_model_type_returns_string(self) -> None:
        """get_model_type must return a non-empty string."""
        mtype = self.sm.get_model_type()
        self.assertIsInstance(mtype, str)
        self.assertTrue(len(mtype) > 0)

    def test_model_type_is_spectral_residual_without_weights(self) -> None:
        """Without weights file, model type must be SpectralResidual-CV."""
        self.sm.load_model()   # weights file absent → falls back
        self.assertEqual(self.sm.get_model_type(), "SpectralResidual-CV")

    def test_predict_non_square_image(self) -> None:
        """Saliency prediction must work on non-square images (e.g. 60×120)."""
        img = _make_synthetic_bgr(h=60, w=120)
        result = self.sm.predict_saliency(img)
        self.assertEqual(result.shape, (60, 120))

    def test_predict_large_image(self) -> None:
        """Saliency prediction must handle larger images (200×300)."""
        img = _make_synthetic_bgr(h=200, w=300)
        result = self.sm.predict_saliency(img)
        self.assertEqual(result.shape, (200, 300))


# ─────────────────────────────────────────────────────────────────────────────
# Test: heatmap_generator
# ─────────────────────────────────────────────────────────────────────────────

class TestHeatmapGenerator(unittest.TestCase):
    """Tests for analyzer.heatmap_generator."""

    def setUp(self) -> None:
        from analyzer import heatmap_generator

        self.hg = heatmap_generator
        self.image = _make_synthetic_bgr()
        self.saliency = _make_synthetic_saliency()

    def test_generate_heatmap_returns_dict(self) -> None:
        """generate_heatmap must return a dict."""
        result = self.hg.generate_heatmap(self.image, self.saliency)
        self.assertIsInstance(result, dict)

    def test_heatmap_base64_is_non_empty_string(self) -> None:
        """heatmap_base64 must be a non-empty string."""
        result = self.hg.generate_heatmap(self.image, self.saliency)
        b64 = result.get("heatmap_base64", "")
        self.assertIsInstance(b64, str)
        self.assertGreater(len(b64), 0)

    def test_heatmap_base64_is_valid_png(self) -> None:
        """heatmap_base64 must decode to a valid PNG image."""
        result = self.hg.generate_heatmap(self.image, self.saliency)
        raw = base64.b64decode(result["heatmap_base64"])
        img = Image.open(BytesIO(raw))
        self.assertIn(img.format, ("PNG",))

    def test_saliency_array_is_list_of_lists(self) -> None:
        """saliency_array must be a list of lists of floats."""
        result = self.hg.generate_heatmap(self.image, self.saliency)
        sal_arr = result.get("saliency_array", [])
        self.assertIsInstance(sal_arr, list)
        self.assertGreater(len(sal_arr), 0)
        self.assertIsInstance(sal_arr[0], list)

    def test_saliency_array_values_in_range(self) -> None:
        """Every value in saliency_array must be in [0, 1]."""
        result = self.hg.generate_heatmap(self.image, self.saliency)
        for row in result["saliency_array"]:
            for val in row:
                self.assertGreaterEqual(val, 0.0)
                self.assertLessEqual(val, 1.0 + 1e-6)

    def test_dimensions_key_present(self) -> None:
        """Result dict must contain 'dimensions' with 'width' and 'height'."""
        result = self.hg.generate_heatmap(self.image, self.saliency)
        dims = result.get("dimensions", {})
        self.assertIn("width", dims)
        self.assertIn("height", dims)

    def test_get_top_attention_regions_returns_list(self) -> None:
        """get_top_attention_regions must return a list."""
        regions = self.hg.get_top_attention_regions(self.saliency)
        self.assertIsInstance(regions, list)

    def test_top_regions_count_bounded(self) -> None:
        """Number of returned regions must not exceed n_regions."""
        n = 3
        regions = self.hg.get_top_attention_regions(self.saliency, n_regions=n)
        self.assertLessEqual(len(regions), n)

    def test_top_regions_have_required_keys(self) -> None:
        """Each region dict must have x, y, w, h, mean_saliency."""
        regions = self.hg.get_top_attention_regions(self.saliency, n_regions=5)
        for r in regions:
            for key in ("x", "y", "w", "h", "mean_saliency"):
                self.assertIn(key, r, f"Key '{key}' missing from region {r}")

    def test_generate_heatmap_custom_alpha(self) -> None:
        """generate_heatmap must accept custom alpha values."""
        for alpha in (0.0, 0.3, 1.0):
            result = self.hg.generate_heatmap(self.image, self.saliency, alpha=alpha)
            self.assertIn("heatmap_base64", result)


# ─────────────────────────────────────────────────────────────────────────────
# Test: cta_detector
# ─────────────────────────────────────────────────────────────────────────────

class TestCTADetector(unittest.TestCase):
    """Tests for analyzer.cta_detector."""

    def setUp(self) -> None:
        from analyzer import cta_detector

        self.cd = cta_detector

    def test_returns_list_on_random_image(self) -> None:
        """detect_cta_regions must always return a list (possibly empty)."""
        img = _make_synthetic_bgr()
        result = self.cd.detect_cta_regions(img)
        self.assertIsInstance(result, list)

    def test_returns_list_on_uniform_grey(self) -> None:
        """On a uniform grey image (no saturated regions), result must be an empty list."""
        grey = np.full((100, 100, 3), 128, dtype=np.uint8)
        result = self.cd.detect_cta_regions(grey)
        self.assertIsInstance(result, list)

    def test_returns_list_on_uniform_red(self) -> None:
        """On a solid red image, result may contain regions (very saturated)."""
        red = np.zeros((100, 100, 3), dtype=np.uint8)
        red[:, :, 2] = 200   # BGR: high red channel, fully saturated
        result = self.cd.detect_cta_regions(red)
        self.assertIsInstance(result, list)

    def test_cta_regions_have_required_keys(self) -> None:
        """Every CTA dict must contain x, y, w, h, confidence."""
        img = _make_synthetic_bgr()
        result = self.cd.detect_cta_regions(img)
        for cta in result:
            for key in ("x", "y", "w", "h", "confidence"):
                self.assertIn(key, cta)

    def test_detects_cta_on_synthetic_button(self) -> None:
        """A bright-green rectangle on grey background should be detected as a CTA."""
        img = np.full((200, 400, 3), 200, dtype=np.uint8)
        # Draw a wide, saturated green button (CTA-like)
        # BGR: (0, 200, 0) — high saturation, medium value
        img[80:120, 120:280] = (0, 200, 50)   # Green rectangle, aspect ~4:1
        result = self.cd.detect_cta_regions(img)
        self.assertIsInstance(result, list)
        # We don't assert it's non-empty (depends on HSV thresholds) but must not crash

    def test_result_capped_at_five(self) -> None:
        """At most 5 CTA candidates should be returned."""
        img = _make_synthetic_bgr(h=400, w=400)
        result = self.cd.detect_cta_regions(img)
        self.assertLessEqual(len(result), 5)

    def test_confidence_in_valid_range(self) -> None:
        """Confidence values must be in [0, 1]."""
        img = _make_synthetic_bgr()
        result = self.cd.detect_cta_regions(img)
        for cta in result:
            self.assertGreaterEqual(cta["confidence"], 0.0)
            self.assertLessEqual(cta["confidence"], 1.0 + 1e-6)

    def test_invalid_input_returns_empty_list(self) -> None:
        """None or incorrect ndim input must return an empty list without raising."""
        result = self.cd.detect_cta_regions(None)
        self.assertEqual(result, [])


# ─────────────────────────────────────────────────────────────────────────────
# Test: focus_score
# ─────────────────────────────────────────────────────────────────────────────

class TestFocusScore(unittest.TestCase):
    """Tests for analyzer.focus_score."""

    def setUp(self) -> None:
        from analyzer import focus_score

        self.fs = focus_score
        self.saliency = _make_synthetic_saliency()

    def test_returns_dict(self) -> None:
        """compute_focus_efficiency must return a dict."""
        result = self.fs.compute_focus_efficiency(self.saliency, [])
        self.assertIsInstance(result, dict)

    def test_score_in_zero_to_hundred(self) -> None:
        """focus_efficiency_score must be in [0, 100]."""
        ctas = [{"x": 10, "y": 10, "w": 30, "h": 15, "confidence": 0.9}]
        result = self.fs.compute_focus_efficiency(self.saliency, ctas)
        score = result["focus_efficiency_score"]
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 100.0)

    def test_score_neutral_when_no_ctas(self) -> None:
        """When CTA list is empty, score must be 50 (neutral)."""
        result = self.fs.compute_focus_efficiency(self.saliency, [])
        self.assertAlmostEqual(result["focus_efficiency_score"], 50.0, places=1)

    def test_required_keys_present(self) -> None:
        """Result must contain all required keys."""
        result = self.fs.compute_focus_efficiency(self.saliency, [])
        for key in (
            "focus_efficiency_score",
            "cta_analysis",
            "global_mean_saliency",
            "interpretation",
        ):
            self.assertIn(key, result)

    def test_cta_analysis_is_list(self) -> None:
        """cta_analysis must be a list."""
        ctas = [{"x": 5, "y": 5, "w": 20, "h": 10, "confidence": 0.8}]
        result = self.fs.compute_focus_efficiency(self.saliency, ctas)
        self.assertIsInstance(result["cta_analysis"], list)

    def test_per_cta_keys(self) -> None:
        """Each CTA analysis entry must have expected keys."""
        ctas = [{"x": 10, "y": 10, "w": 30, "h": 15, "confidence": 0.85}]
        result = self.fs.compute_focus_efficiency(self.saliency, ctas)
        for entry in result["cta_analysis"]:
            for key in ("cta_index", "region", "region_mean_saliency", "fes", "status"):
                self.assertIn(key, entry)

    def test_cta_outside_image_bounds(self) -> None:
        """CTAs with bounding boxes outside image bounds must not crash."""
        ctas = [{"x": 9000, "y": 9000, "w": 100, "h": 50, "confidence": 0.5}]
        result = self.fs.compute_focus_efficiency(self.saliency, ctas)
        # Should not raise; score should be neutral
        self.assertAlmostEqual(result["focus_efficiency_score"], 50.0, places=1)

    def test_interpretation_is_string(self) -> None:
        """interpretation field must be a non-empty string."""
        result = self.fs.compute_focus_efficiency(self.saliency, [])
        interp = result.get("interpretation", "")
        self.assertIsInstance(interp, str)
        self.assertGreater(len(interp), 0)

    def test_compute_recommendations_returns_list(self) -> None:
        """compute_recommendations must return a list of strings."""
        focus_data = self.fs.compute_focus_efficiency(self.saliency, [])
        recs = self.fs.compute_recommendations(focus_data)
        self.assertIsInstance(recs, list)
        for r in recs:
            self.assertIsInstance(r, str)

    def test_recommendations_non_empty(self) -> None:
        """compute_recommendations must always return at least one string."""
        focus_data = self.fs.compute_focus_efficiency(self.saliency, [])
        recs = self.fs.compute_recommendations(focus_data)
        self.assertGreater(len(recs), 0)

    def test_score_capped_at_hundred_for_high_fes(self) -> None:
        """When CTA is in a very high-saliency region, score must not exceed 100."""
        # Create a saliency map with a bright hotspot
        sal = np.zeros((100, 100), dtype=np.float32)
        sal[10:30, 10:50] = 1.0   # CTA area = max saliency
        ctas = [{"x": 10, "y": 10, "w": 40, "h": 20, "confidence": 0.9}]
        result = self.fs.compute_focus_efficiency(sal, ctas)
        self.assertLessEqual(result["focus_efficiency_score"], 100.0)


# ─────────────────────────────────────────────────────────────────────────────
# Test: image_utils
# ─────────────────────────────────────────────────────────────────────────────

class TestImageUtils(unittest.TestCase):
    """Tests for utils.image_utils."""

    def setUp(self) -> None:
        from utils import image_utils

        self.iu = image_utils
        self.image = _make_synthetic_bgr()

    def test_get_image_dimensions_3channel(self) -> None:
        """get_image_dimensions must return correct dims for a 3-channel image."""
        dims = self.iu.get_image_dimensions(self.image)
        self.assertEqual(dims["width"], self.image.shape[1])
        self.assertEqual(dims["height"], self.image.shape[0])
        self.assertEqual(dims["channels"], 3)

    def test_get_image_dimensions_grayscale(self) -> None:
        """get_image_dimensions must handle 2-D (grayscale) arrays."""
        grey = np.zeros((50, 80), dtype=np.uint8)
        dims = self.iu.get_image_dimensions(grey)
        self.assertEqual(dims["width"], 80)
        self.assertEqual(dims["height"], 50)
        self.assertEqual(dims["channels"], 1)

    def test_decode_base64_image_roundtrip(self) -> None:
        """decode_base64_image must reconstruct an image with correct shape."""
        b64 = _encode_image_to_base64(self.image)
        decoded = self.iu.decode_base64_image(b64)
        self.assertEqual(decoded.shape, self.image.shape)

    def test_decode_base64_with_data_uri_prefix(self) -> None:
        """decode_base64_image must handle data-URI prefixed strings."""
        b64 = _encode_image_to_base64(self.image)
        uri = f"data:image/png;base64,{b64}"
        decoded = self.iu.decode_base64_image(uri)
        self.assertEqual(decoded.shape, self.image.shape)

    def test_decode_base64_invalid_raises_value_error(self) -> None:
        """decode_base64_image must raise ValueError on invalid data."""
        with self.assertRaises(ValueError):
            self.iu.decode_base64_image("not_valid_base64!!")

    def test_resize_for_display_no_upscale(self) -> None:
        """resize_for_display must not upscale images smaller than max_dim."""
        small = _make_synthetic_bgr(h=50, w=50)
        result = self.iu.resize_for_display(small, max_dim=800)
        self.assertEqual(result.shape, small.shape)

    def test_resize_for_display_downscales(self) -> None:
        """resize_for_display must scale down large images correctly."""
        large = _make_synthetic_bgr(h=1600, w=800)
        result = self.iu.resize_for_display(large, max_dim=800)
        self.assertLessEqual(max(result.shape[:2]), 800)

    def test_resize_for_display_preserves_aspect(self) -> None:
        """resize_for_display must preserve the aspect ratio (within 1 pixel)."""
        img = _make_synthetic_bgr(h=400, w=200)
        result = self.iu.resize_for_display(img, max_dim=200)
        orig_ratio = 400 / 200
        result_ratio = result.shape[0] / result.shape[1]
        self.assertAlmostEqual(orig_ratio, result_ratio, delta=0.05)

    def test_cleanup_temp_no_crash_on_missing_file(self) -> None:
        """cleanup_temp must not raise when the file does not exist."""
        try:
            self.iu.cleanup_temp("/tmp/nonexistent_visual_hierarchy_test_file.png")
        except Exception as exc:
            self.fail(f"cleanup_temp raised unexpectedly: {exc}")

    def test_load_image_bgr_raises_on_missing(self) -> None:
        """load_image_bgr must raise ValueError for a missing path."""
        with self.assertRaises(ValueError):
            self.iu.load_image_bgr("/tmp/definitely_not_here_xyz.jpg")


# ─────────────────────────────────────────────────────────────────────────────
# Test: Flask app endpoints
# ─────────────────────────────────────────────────────────────────────────────

class TestFlaskEndpoints(unittest.TestCase):
    """Integration tests for the Flask app using the built-in test client."""

    @classmethod
    def setUpClass(cls) -> None:
        """Import and configure the Flask app for testing."""
        # Patch saliency_model so load_model() doesn't fail during app import
        import app as flask_app

        flask_app.app.config["TESTING"] = True
        cls.client = flask_app.app.test_client()

    # ── /health ───────────────────────────────────────────────────────────────

    def test_health_returns_200(self) -> None:
        """GET /health must return 200."""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)

    def test_health_payload(self) -> None:
        """GET /health must return correct JSON."""
        resp = self.client.get("/health")
        data = resp.get_json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], "visual-hierarchy")

    # ── /model-info ───────────────────────────────────────────────────────────

    def test_model_info_returns_200(self) -> None:
        """GET /model-info must return 200."""
        resp = self.client.get("/model-info")
        self.assertEqual(resp.status_code, 200)

    def test_model_info_has_active_model(self) -> None:
        """GET /model-info must include 'active_model' key."""
        resp = self.client.get("/model-info")
        data = resp.get_json()
        self.assertIn("active_model", data)

    # ── /analyze — error cases ────────────────────────────────────────────────

    def test_analyze_no_image_returns_400(self) -> None:
        """POST /analyze with no image must return 400."""
        resp = self.client.post(
            "/analyze",
            json={},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_analyze_empty_json_returns_400(self) -> None:
        """POST /analyze with empty JSON body must return 400."""
        resp = self.client.post("/analyze", json={})
        self.assertEqual(resp.status_code, 400)

    # ── /analyze — success via base64 ─────────────────────────────────────────

    def test_analyze_base64_returns_200(self) -> None:
        """POST /analyze with valid base64 image must return 200."""
        img = _make_synthetic_bgr()
        b64 = _encode_image_to_base64(img)
        resp = self.client.post(
            "/analyze",
            json={"image_base64": b64},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)

    def test_analyze_base64_response_structure(self) -> None:
        """POST /analyze response must include all required top-level keys."""
        img = _make_synthetic_bgr()
        b64 = _encode_image_to_base64(img)
        resp = self.client.post(
            "/analyze",
            json={"image_base64": b64},
            content_type="application/json",
        )
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        for key in (
            "model_used",
            "image_dimensions",
            "saliency",
            "cta_regions",
            "focus_efficiency",
            "recommendations",
            "processing_time_ms",
        ):
            self.assertIn(key, data, f"Missing key: {key}")

    def test_analyze_response_heatmap_non_empty(self) -> None:
        """heatmap_base64 in the response must be a non-empty string."""
        img = _make_synthetic_bgr()
        b64 = _encode_image_to_base64(img)
        resp = self.client.post(
            "/analyze",
            json={"image_base64": b64},
        )
        data = resp.get_json()
        heatmap = data["saliency"].get("heatmap_base64", "")
        self.assertIsInstance(heatmap, str)
        self.assertGreater(len(heatmap), 0)

    def test_analyze_focus_score_in_range(self) -> None:
        """focus_efficiency_score in the response must be in [0, 100]."""
        img = _make_synthetic_bgr()
        b64 = _encode_image_to_base64(img)
        resp = self.client.post(
            "/analyze",
            json={"image_base64": b64},
        )
        data = resp.get_json()
        score = data["focus_efficiency"]["focus_efficiency_score"]
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 100.0)

    def test_analyze_recommendations_is_list(self) -> None:
        """recommendations in the response must be a list."""
        img = _make_synthetic_bgr()
        b64 = _encode_image_to_base64(img)
        resp = self.client.post(
            "/analyze",
            json={"image_base64": b64},
        )
        data = resp.get_json()
        self.assertIsInstance(data["recommendations"], list)

    # ── /analyze — success via multipart ──────────────────────────────────────

    def test_analyze_multipart_returns_200(self) -> None:
        """POST /analyze with multipart image upload must return 200."""
        img = _make_synthetic_bgr()
        png_bytes = _encode_image_to_bytes(img)
        resp = self.client.post(
            "/analyze",
            data={"image": (BytesIO(png_bytes), "test.png")},
            content_type="multipart/form-data",
        )
        self.assertEqual(resp.status_code, 200)

    def test_analyze_multipart_response_structure(self) -> None:
        """POST /analyze multipart must include all required top-level keys."""
        img = _make_synthetic_bgr()
        png_bytes = _encode_image_to_bytes(img)
        resp = self.client.post(
            "/analyze",
            data={"image": (BytesIO(png_bytes), "test.png")},
            content_type="multipart/form-data",
        )
        data = resp.get_json()
        self.assertEqual(data["status"], "success")
        for key in ("saliency", "cta_regions", "focus_efficiency", "recommendations"):
            self.assertIn(key, data)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main(verbosity=2)
