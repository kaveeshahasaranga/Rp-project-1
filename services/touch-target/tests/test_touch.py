"""
Unit tests for the touch-target evaluator modules.

All tests use mock element dictionaries — no network calls or browser
instances are required.

Run with:  pytest services/touch-target/tests/test_touch.py -v
"""

from __future__ import annotations

import math

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------

def _el(w: int, h: int, x: int = 0, y: int = 0, tag: str = "button",
        display: str = "block", visibility: str = "visible",
        opacity: str = "1") -> dict:
    """Construct a minimal mock element dict."""
    return {
        "tag": tag,
        "role": "",
        "text": "Click me",
        "x": x,
        "y": y,
        "width": w,
        "height": h,
        "display": display,
        "visibility": visibility,
        "opacity": opacity,
    }


# ---------------------------------------------------------------------------
# WCAG checker tests
# ---------------------------------------------------------------------------

class TestWcagChecker:
    """Tests for analyzer.wcag_checker.check_element and compute_compliance_stats."""

    # ---- check_element ----

    def test_check_element_returns_dict(self):
        """check_element must return a dict."""
        from analyzer.wcag_checker import check_element
        result = check_element(_el(48, 48))
        assert isinstance(result, dict)

    def test_check_element_adds_required_keys(self):
        """check_element result must contain the four new keys."""
        from analyzer.wcag_checker import check_element
        result = check_element(_el(50, 50))
        for key in ("wcag_aa_pass", "wcag_aaa_pass", "recommended_pass", "issues"):
            assert key in result, f"Missing key: {key}"

    def test_aaa_fail_below_44(self):
        """An element smaller than 44×44 px should fail WCAG AAA."""
        from analyzer.wcag_checker import check_element
        result = check_element(_el(30, 30))
        assert result["wcag_aaa_pass"] is False, "30×30 should fail AAA (44px minimum)"

    def test_aaa_pass_at_44(self):
        """An element exactly 44×44 px should pass WCAG AAA."""
        from analyzer.wcag_checker import check_element
        result = check_element(_el(44, 44))
        assert result["wcag_aaa_pass"] is True, "44×44 should pass AAA"

    def test_aaa_pass_above_44(self):
        """An element 60×60 px should pass WCAG AAA."""
        from analyzer.wcag_checker import check_element
        result = check_element(_el(60, 60))
        assert result["wcag_aaa_pass"] is True, "60×60 should pass AAA"

    def test_aa_fail_below_24(self):
        """An element smaller than 24×24 px should fail WCAG AA."""
        from analyzer.wcag_checker import check_element
        result = check_element(_el(20, 20))
        assert result["wcag_aa_pass"] is False, "20×20 should fail AA (24px minimum)"

    def test_aa_pass_at_24(self):
        """An element exactly 24×24 px should pass WCAG AA."""
        from analyzer.wcag_checker import check_element
        result = check_element(_el(24, 24))
        assert result["wcag_aa_pass"] is True, "24×24 should pass AA"

    def test_recommended_fail_below_48(self):
        """An element smaller than 48×48 px should fail the recommended threshold."""
        from analyzer.wcag_checker import check_element
        result = check_element(_el(44, 44))
        assert result["recommended_pass"] is False, "44×44 should fail recommended (48px)"

    def test_recommended_pass_at_48(self):
        """An element 48×48 px should pass the recommended threshold."""
        from analyzer.wcag_checker import check_element
        result = check_element(_el(48, 48))
        assert result["recommended_pass"] is True, "48×48 should pass recommended"

    def test_issues_populated_for_small_element(self):
        """A very small element should have at least one issue string."""
        from analyzer.wcag_checker import check_element
        result = check_element(_el(10, 10))
        assert len(result["issues"]) > 0, "10×10 element should have issues"

    def test_no_issues_for_large_element(self):
        """A 48×48 element should have no issues."""
        from analyzer.wcag_checker import check_element
        result = check_element(_el(48, 48))
        # 48×48 passes AA (≥24) and AAA (≥44) and recommended (≥48)
        assert result["wcag_aa_pass"] is True
        assert result["wcag_aaa_pass"] is True
        assert result["recommended_pass"] is True
        assert len(result["issues"]) == 0

    # ---- compute_compliance_stats ----

    def test_stats_empty_list(self):
        """compute_compliance_stats on empty list should return 1.0 rates."""
        from analyzer.wcag_checker import compute_compliance_stats
        stats = compute_compliance_stats([])
        assert stats["total_elements"] == 0
        assert stats["wcag_aa_compliance_rate"] == 1.0

    def test_stats_all_pass(self):
        """All 48×48 elements should give 1.0 compliance rates."""
        from analyzer.wcag_checker import check_element, compute_compliance_stats
        elements = [check_element(_el(48, 48)) for _ in range(5)]
        stats = compute_compliance_stats(elements)
        assert stats["wcag_aa_compliance_rate"] == 1.0
        assert stats["wcag_aaa_compliance_rate"] == 1.0
        assert stats["recommended_compliance_rate"] == 1.0
        assert stats["violations"] == []

    def test_stats_all_fail(self):
        """All 10×10 elements should give 0.0 AA compliance rate."""
        from analyzer.wcag_checker import check_element, compute_compliance_stats
        elements = [check_element(_el(10, 10)) for _ in range(4)]
        stats = compute_compliance_stats(elements)
        assert stats["wcag_aa_compliance_rate"] == 0.0
        assert len(stats["violations"]) == 4

    def test_stats_mixed(self):
        """Half-pass, half-fail should give 0.5 AA compliance rate."""
        from analyzer.wcag_checker import check_element, compute_compliance_stats
        elements = [check_element(_el(48, 48)) for _ in range(3)]
        elements += [check_element(_el(10, 10)) for _ in range(3)]
        stats = compute_compliance_stats(elements)
        assert abs(stats["wcag_aa_compliance_rate"] - 0.5) < 1e-6


# ---------------------------------------------------------------------------
# Fitts's Law tests
# ---------------------------------------------------------------------------

class TestFittsLaw:
    """Tests for analyzer.fitts_law.compute_id and analyze_fitts_compliance."""

    def test_compute_id_square_target(self):
        """A perfectly square target should have ID = 1.0 (log2(2*1) = 1)."""
        from analyzer.fitts_law import compute_id
        # max=50, min=50 → ID = log2(100/50) = log2(2) = 1.0
        result = compute_id(50.0, 50.0)
        assert abs(result - 1.0) < 1e-9, f"Square target ID should be 1.0, got {result}"

    def test_compute_id_tall_target(self):
        """A 10×100 target should have a higher ID than a 50×50 target."""
        from analyzer.fitts_law import compute_id
        id_tall = compute_id(10.0, 100.0)
        id_square = compute_id(50.0, 50.0)
        assert id_tall > id_square, (
            f"Tall/narrow target ({id_tall}) should be harder than square ({id_square})"
        )

    def test_compute_id_positive(self):
        """ID should be non-negative for any positive dimensions."""
        from analyzer.fitts_law import compute_id
        for w, h in [(1, 1), (5, 50), (100, 10), (48, 48)]:
            result = compute_id(w, h)
            assert result >= 0.0, f"ID should be ≥ 0 for {w}×{h}, got {result}"

    def test_analyze_returns_dict(self):
        """analyze_fitts_compliance must return a dict."""
        from analyzer.fitts_law import analyze_fitts_compliance
        from analyzer.wcag_checker import check_element
        elements = [check_element(_el(48, 48))]
        result = analyze_fitts_compliance(elements)
        assert isinstance(result, dict)

    def test_analyze_required_keys(self):
        """Result must contain all required keys."""
        from analyzer.fitts_law import analyze_fitts_compliance
        from analyzer.wcag_checker import check_element
        elements = [check_element(_el(44, 44))]
        result = analyze_fitts_compliance(elements)
        for key in ("mean_id", "max_id", "violations", "fitts_compliance_score",
                    "id_violation_threshold"):
            assert key in result, f"Missing key: {key}"

    def test_compliance_score_range(self):
        """fitts_compliance_score must be in [0, 100]."""
        from analyzer.fitts_law import analyze_fitts_compliance
        from analyzer.wcag_checker import check_element
        elements = [check_element(_el(w, h)) for w, h in [(10, 100), (48, 48), (20, 20)]]
        result = analyze_fitts_compliance(elements)
        score = result["fitts_compliance_score"]
        assert 0.0 <= score <= 100.0, f"Score out of range: {score}"

    def test_all_square_targets_no_violations(self):
        """All 48×48 square targets should have zero Fitts violations (ID=1.0 < 3.5)."""
        from analyzer.fitts_law import analyze_fitts_compliance
        from analyzer.wcag_checker import check_element
        elements = [check_element(_el(48, 48)) for _ in range(5)]
        result = analyze_fitts_compliance(elements)
        assert result["violations"] == [], f"Expected no violations, got {result['violations']}"
        assert result["fitts_compliance_score"] == 100.0

    def test_empty_elements_returns_defaults(self):
        """Empty element list should return 100 score and no violations."""
        from analyzer.fitts_law import analyze_fitts_compliance
        result = analyze_fitts_compliance([])
        assert result["fitts_compliance_score"] == 100.0
        assert result["violations"] == []


# ---------------------------------------------------------------------------
# Clustering tests
# ---------------------------------------------------------------------------

class TestClustering:
    """Tests for analyzer.clustering.detect_accidental_click_clusters."""

    def _make_cluster(self, cx: float, cy: float, n: int = 5,
                      spread: float = 10.0) -> list[dict]:
        """Create n elements densely packed around (cx, cy)."""
        rng = np.random.default_rng(seed=int(cx + cy))
        elements: list[dict] = []
        for _ in range(n):
            offset_x = float(rng.uniform(-spread / 2, spread / 2))
            offset_y = float(rng.uniform(-spread / 2, spread / 2))
            elements.append(_el(
                w=24, h=24,
                x=int(cx + offset_x - 12),
                y=int(cy + offset_y - 12),
            ))
        return elements

    def test_returns_dict(self):
        """detect_accidental_click_clusters must return a dict."""
        from analyzer.clustering import detect_accidental_click_clusters
        result = detect_accidental_click_clusters([])
        assert isinstance(result, dict)

    def test_required_keys(self):
        """Result must contain required keys."""
        from analyzer.clustering import detect_accidental_click_clusters
        result = detect_accidental_click_clusters([])
        for key in ("n_clusters", "accidental_click_clusters", "risk_level", "parameters"):
            assert key in result, f"Missing key: {key}"

    def test_empty_elements_low_risk(self):
        """No elements should yield risk_level = 'low'."""
        from analyzer.clustering import detect_accidental_click_clusters
        result = detect_accidental_click_clusters([])
        assert result["risk_level"] == "low"
        assert result["n_clusters"] == 0

    def test_widely_spaced_elements_no_clusters(self):
        """Elements 200 px apart should not form any clusters."""
        from analyzer.clustering import detect_accidental_click_clusters
        elements = [_el(w=48, h=48, x=i * 200, y=0) for i in range(6)]
        result = detect_accidental_click_clusters(elements)
        # Well-separated buttons should not cluster (they need min_samples=3)
        # Each is isolated — DBSCAN labels them as noise
        assert result["n_clusters"] == 0
        assert result["risk_level"] == "low"

    def test_one_dense_cluster_detected(self):
        """Five elements densely packed in one spot should form one cluster."""
        from analyzer.clustering import detect_accidental_click_clusters
        elements = self._make_cluster(cx=100.0, cy=100.0, n=5)
        result = detect_accidental_click_clusters(elements)
        assert result["n_clusters"] == 1
        assert result["risk_level"] == "moderate"

    def test_two_dense_clusters_detected(self):
        """Two groups of dense elements should form two clusters → moderate risk."""
        from analyzer.clustering import detect_accidental_click_clusters
        group_a = self._make_cluster(cx=100.0, cy=100.0, n=5)
        group_b = self._make_cluster(cx=500.0, cy=500.0, n=5)
        elements = group_a + group_b
        result = detect_accidental_click_clusters(elements)
        assert result["n_clusters"] == 2
        assert result["risk_level"] == "moderate"

    def test_three_clusters_high_risk(self):
        """Three dense clusters should yield risk_level = 'high'."""
        from analyzer.clustering import detect_accidental_click_clusters
        elements = (
            self._make_cluster(cx=100.0, cy=100.0, n=5)
            + self._make_cluster(cx=500.0, cy=100.0, n=5)
            + self._make_cluster(cx=300.0, cy=500.0, n=5)
        )
        result = detect_accidental_click_clusters(elements)
        assert result["n_clusters"] == 3
        assert result["risk_level"] == "high"

    def test_cluster_summary_has_centroid(self):
        """Each cluster summary must have 'centroid' and 'element_count' keys."""
        from analyzer.clustering import detect_accidental_click_clusters
        elements = self._make_cluster(cx=200.0, cy=200.0, n=6)
        result = detect_accidental_click_clusters(elements)
        for cluster in result["accidental_click_clusters"]:
            assert "centroid" in cluster
            assert "element_count" in cluster
            assert isinstance(cluster["centroid"], list)
            assert len(cluster["centroid"]) == 2


# ---------------------------------------------------------------------------
# Geometry utilities tests
# ---------------------------------------------------------------------------

class TestGeometryUtils:
    """Tests for utils.geometry_utils."""

    def test_euclidean_distance_same_point(self):
        from utils.geometry_utils import euclidean_distance
        assert euclidean_distance((0.0, 0.0), (0.0, 0.0)) == 0.0

    def test_euclidean_distance_known_value(self):
        from utils.geometry_utils import euclidean_distance
        result = euclidean_distance((0.0, 0.0), (3.0, 4.0))
        assert abs(result - 5.0) < 1e-9

    def test_centroid_of_unit_square(self):
        from utils.geometry_utils import centroid
        cx, cy = centroid(0.0, 0.0, 2.0, 2.0)
        assert cx == 1.0 and cy == 1.0

    def test_area_positive(self):
        from utils.geometry_utils import area
        assert area(10.0, 5.0) == 50.0

    def test_area_zero_for_negative(self):
        from utils.geometry_utils import area
        assert area(-1.0, 5.0) == 0.0

    def test_is_visible_true(self):
        from utils.geometry_utils import is_visible
        assert is_visible(_el(48, 48)) is True

    def test_is_visible_hidden_display(self):
        from utils.geometry_utils import is_visible
        assert is_visible(_el(48, 48, display="none")) is False

    def test_is_visible_hidden_visibility(self):
        from utils.geometry_utils import is_visible
        assert is_visible(_el(48, 48, visibility="hidden")) is False

    def test_is_visible_zero_opacity(self):
        from utils.geometry_utils import is_visible
        assert is_visible(_el(48, 48, opacity="0")) is False
