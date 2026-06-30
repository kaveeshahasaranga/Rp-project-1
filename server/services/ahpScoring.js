'use strict';

/**
 * AHP Scoring Engine
 * ──────────────────
 * Analytic Hierarchy Process weights derived from the following
 * pairwise comparison matrix (Saaty 1–9 scale):
 *
 *             CL      VH      TT
 *   CL    [ 1.000   2.000   3.000 ]
 *   VH    [ 0.500   1.000   2.000 ]
 *   TT    [ 0.333   0.500   1.000 ]
 *
 * Column sums: [1.833, 3.500, 6.000]
 * Normalised & averaged → weights below.
 * λ_max ≈ 3.009  →  CI = (3.009-3)/(3-1) = 0.0045
 * RI(n=3) = 0.52  →  CR = CI/RI ≈ 0.009  ✅ (< 0.10)
 */

const AHP_WEIGHTS = Object.freeze({
  cognitive_load:   0.5396,
  visual_hierarchy: 0.2970,
  touch_target:     0.1634
});

/** Saaty Random Index table (index = n) */
const RI_TABLE = Object.freeze({ 1: 0, 2: 0, 3: 0.52, 4: 0.89, 5: 1.12 });

/**
 * Compute the AHP-weighted composite UX score.
 *
 * @param {{
 *   cognitive_load?:   number,
 *   visual_hierarchy?: number,
 *   touch_target?:     number
 * }} scores  Each value is expected in the range [0, 100].
 *
 * @returns {{
 *   composite_score:    number,
 *   grade:              'A'|'B'|'C'|'D'|'F',
 *   weights:            typeof AHP_WEIGHTS,
 *   consistency_ratio:  number,
 *   breakdown:          { cognitive_load: number, visual_hierarchy: number, touch_target: number }
 * }}
 */
function computeAHPScore(scores = {}) {
  const cognitive_load   = Math.max(0, Math.min(100, Number(scores.cognitive_load)   || 0));
  const visual_hierarchy = Math.max(0, Math.min(100, Number(scores.visual_hierarchy) || 0));
  const touch_target     = Math.max(0, Math.min(100, Number(scores.touch_target)     || 0));

  const raw = (
    AHP_WEIGHTS.cognitive_load   * cognitive_load   +
    AHP_WEIGHTS.visual_hierarchy * visual_hierarchy +
    AHP_WEIGHTS.touch_target     * touch_target
  );

  const composite_score = Math.round(raw * 10) / 10; // 1 decimal place

  const grade =
    composite_score >= 90 ? 'A' :
    composite_score >= 75 ? 'B' :
    composite_score >= 55 ? 'C' :
    composite_score >= 35 ? 'D' : 'F';

  return {
    composite_score,
    grade,
    weights: AHP_WEIGHTS,
    consistency_ratio: 0.009, // Pre-validated — CR < 0.10
    breakdown: { cognitive_load, visual_hierarchy, touch_target }
  };
}

module.exports = { computeAHPScore, AHP_WEIGHTS, RI_TABLE };
