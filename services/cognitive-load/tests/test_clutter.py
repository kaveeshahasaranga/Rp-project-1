"""
Unit tests for the cognitive-load analyzer modules.

Run with:  pytest services/cognitive-load/tests/test_clutter.py -v
"""

from __future__ import annotations

import os
import tempfile

import cv2
import numpy as np
import pytest

# ---------------------------------------------------------------------------
# Helpers — create synthetic test images
# ---------------------------------------------------------------------------

def _make_solid_image(path: str, color: tuple[int, int, int] = (128, 128, 128),
                      size: tuple[int, int] = (128, 128)) -> str:
    """Write a solid-colour BGR image to *path* and return the path."""
    img = np.full((size[1], size[0], 3), color, dtype=np.uint8)
    cv2.imwrite(path, img)
    return path


def _make_random_image(path: str, size: tuple[int, int] = (128, 128)) -> str:
    """Write a random-noise BGR image to *path* and return the path."""
    rng = np.random.default_rng(seed=42)
    img = rng.integers(0, 256, (size[1], size[0], 3), dtype=np.uint8)
    cv2.imwrite(path, img)
    return path


def _make_checkerboard_image(path: str, size: int = 128, tile: int = 8) -> str:
    """Write a black-and-white checkerboard image to *path* and return the path."""
    img = np.zeros((size, size, 3), dtype=np.uint8)
    for r in range(0, size, tile):
        for c in range(0, size, tile):
            if (r // tile + c // tile) % 2 == 0:
                img[r:r + tile, c:c + tile] = 255
    cv2.imwrite(path, img)
    return path


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def solid_image_path():
    """Solid grey 128×128 image."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        path = f.name
    _make_solid_image(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture(scope="module")
def random_image_path():
    """Random-noise 128×128 image."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        path = f.name
    _make_random_image(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture(scope="module")
def checkerboard_image_path():
    """High-edge-density checkerboard image."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        path = f.name
    _make_checkerboard_image(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


# ---------------------------------------------------------------------------
# edge_density tests
# ---------------------------------------------------------------------------

class TestEdgeDensity:
    """Tests for analyzer.edge_density.compute_edge_density."""

    def test_returns_float(self, solid_image_path):
        """compute_edge_density must return a float."""
        from analyzer.edge_density import compute_edge_density
        result = compute_edge_density(solid_image_path)
        assert isinstance(result, float), f"Expected float, got {type(result)}"

    def test_in_range(self, random_image_path):
        """Edge density must be in [0, 1]."""
        from analyzer.edge_density import compute_edge_density
        result = compute_edge_density(random_image_path)
        assert 0.0 <= result <= 1.0, f"Edge density out of range: {result}"

    def test_solid_image_low_density(self, solid_image_path):
        """A solid-colour image should have very low edge density."""
        from analyzer.edge_density import compute_edge_density
        result = compute_edge_density(solid_image_path)
        assert result < 0.05, f"Solid image should have near-zero edges, got {result}"

    def test_checkerboard_higher_than_solid(self, checkerboard_image_path, solid_image_path):
        """A checkerboard should have more edges than a solid image."""
        from analyzer.edge_density import compute_edge_density
        cb_density = compute_edge_density(checkerboard_image_path)
        solid_density = compute_edge_density(solid_image_path)
        assert cb_density > solid_density, (
            f"Checkerboard ({cb_density}) should exceed solid ({solid_density})"
        )


# ---------------------------------------------------------------------------
# subband_entropy tests
# ---------------------------------------------------------------------------

class TestSubbandEntropy:
    """Tests for analyzer.subband_entropy.compute_subband_entropy."""

    def test_returns_float(self, solid_image_path):
        """compute_subband_entropy must return a float."""
        from analyzer.subband_entropy import compute_subband_entropy
        result = compute_subband_entropy(solid_image_path)
        assert isinstance(result, float), f"Expected float, got {type(result)}"

    def test_in_range(self, random_image_path):
        """Subband entropy must be in [0, 1]."""
        from analyzer.subband_entropy import compute_subband_entropy
        result = compute_subband_entropy(random_image_path)
        assert 0.0 <= result <= 1.0, f"Subband entropy out of range: {result}"

    def test_random_greater_than_solid(self, random_image_path, solid_image_path):
        """A random noise image should have higher entropy than a solid image."""
        from analyzer.subband_entropy import compute_subband_entropy
        rand_entropy = compute_subband_entropy(random_image_path)
        solid_entropy = compute_subband_entropy(solid_image_path)
        assert rand_entropy > solid_entropy, (
            f"Random ({rand_entropy}) should exceed solid ({solid_entropy})"
        )


# ---------------------------------------------------------------------------
# clutter_score tests
# ---------------------------------------------------------------------------

class TestClutterScore:
    """Tests for analyzer.clutter_score.compute_clutter_score."""

    def test_returns_dict(self):
        """compute_clutter_score must return a dict."""
        from analyzer.clutter_score import compute_clutter_score
        result = compute_clutter_score(0.5, 0.5, 0.5)
        assert isinstance(result, dict), f"Expected dict, got {type(result)}"

    def test_required_keys(self):
        """Result must contain all required top-level keys."""
        from analyzer.clutter_score import compute_clutter_score
        result = compute_clutter_score(0.3, 0.2, 0.4)
        required = {
            "cognitive_load_score", "severity", "raw_metrics",
            "weights_used", "recommendations",
        }
        missing = required - result.keys()
        assert not missing, f"Missing keys: {missing}"

    def test_raw_metrics_keys(self):
        """raw_metrics must contain fc, ed, se sub-keys."""
        from analyzer.clutter_score import compute_clutter_score
        result = compute_clutter_score(0.1, 0.2, 0.3)
        raw = result["raw_metrics"]
        for key in ("feature_congestion", "edge_density", "subband_entropy"):
            assert key in raw, f"Missing raw_metric key: {key}"

    def test_score_in_range(self):
        """cognitive_load_score must be in [0, 100]."""
        from analyzer.clutter_score import compute_clutter_score
        for fc, ed, se in [(0.0, 0.0, 0.0), (1.0, 1.0, 1.0), (0.5, 0.3, 0.7)]:
            result = compute_clutter_score(fc, ed, se)
            score = result["cognitive_load_score"]
            assert 0.0 <= score <= 100.0, f"Score out of range for ({fc},{ed},{se}): {score}"

    def test_severity_low_band(self):
        """Score >= 80 should map to 'low' severity."""
        from analyzer.clutter_score import compute_clutter_score
        # All zeros → score = 100
        result = compute_clutter_score(0.0, 0.0, 0.0)
        assert result["severity"] == "low", (
            f"Expected 'low', got {result['severity']} (score={result['cognitive_load_score']})"
        )

    def test_severity_high_band(self):
        """Score < 55 should map to 'high' severity."""
        from analyzer.clutter_score import compute_clutter_score
        # All ones → raw=1.0 → score=0.0
        result = compute_clutter_score(1.0, 1.0, 1.0)
        assert result["severity"] == "high", (
            f"Expected 'high', got {result['severity']} (score={result['cognitive_load_score']})"
        )

    def test_severity_moderate_band(self):
        """An intermediate input should map to 'moderate' severity."""
        from analyzer.clutter_score import compute_clutter_score
        # raw ≈ 0.40*0.3 + 0.30*0.4 + 0.30*0.5 = 0.12+0.12+0.15 = 0.39 → score ≈ 61
        result = compute_clutter_score(0.3, 0.4, 0.5)
        assert result["severity"] == "moderate", (
            f"Expected 'moderate', got {result['severity']} (score={result['cognitive_load_score']})"
        )

    def test_recommendations_list(self):
        """recommendations must be a non-empty list of strings."""
        from analyzer.clutter_score import compute_clutter_score
        result = compute_clutter_score(0.6, 0.4, 0.6)
        recs = result["recommendations"]
        assert isinstance(recs, list) and len(recs) > 0, "Recommendations should be a non-empty list"
        for rec in recs:
            assert isinstance(rec, str), f"Each recommendation should be a string, got {type(rec)}"

    def test_clean_image_no_recommendations(self):
        """A perfectly clean image (fc=0, ed=0, se=0) should return the 'no changes' message."""
        from analyzer.clutter_score import compute_clutter_score
        result = compute_clutter_score(0.0, 0.0, 0.0)
        recs = result["recommendations"]
        assert len(recs) == 1
        assert "No major changes needed" in recs[0]

    def test_weights_sum_to_one(self):
        """weights_used values must sum to 1.0."""
        from analyzer.clutter_score import compute_clutter_score
        result = compute_clutter_score(0.2, 0.3, 0.4)
        weights = result["weights_used"]
        total = sum(weights.values())
        assert abs(total - 1.0) < 1e-9, f"Weights should sum to 1.0, got {total}"
