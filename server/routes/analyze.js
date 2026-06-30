'use strict';

const express = require('express');
const { z }   = require('zod');
const { v4: uuidv4 } = require('uuid');

const authMiddleware          = require('../middleware/auth');
const { upload }              = require('../middleware/upload');
const { captureScreenshot }   = require('../services/screenshotter');
const { orchestrateAnalysis } = require('../services/orchestrator');
const { computeAHPScore }     = require('../services/ahpScoring');
const AuditReport             = require('../models/AuditReport');

const router = express.Router();

// ─── Input validation schema ──────────────────────────────────────────────────
const analyzeSchema = z.object({
  url: z.string().url('A valid absolute URL is required (include https://).')
});

// ─── Score extraction helpers ─────────────────────────────────────────────────

/**
 * Pull the cognitive load score (0-100) out of the cognitive service response.
 * Accommodates common key variants returned by Python Flask/FastAPI services.
 */
function extractCognitiveScore(data) {
  if (!data) return 0;
  const raw =
    data.cognitive_load_score ??
    data.cognitive_score      ??
    data.score                ??
    data.result?.score        ??
    0;
  return Math.max(0, Math.min(100, Number(raw) || 0));
}

/**
 * Pull the visual hierarchy / saliency score (0-100) from the saliency response.
 */
function extractSaliencyScore(data) {
  if (!data) return 0;
  const raw =
    data.focus_efficiency_score ??
    data.visual_hierarchy_score ??
    data.saliency_score         ??
    data.score                  ??
    data.result?.score          ??
    0;
  return Math.max(0, Math.min(100, Number(raw) || 0));
}

/**
 * Pull the touch target score (0-100) from the touch service response.
 */
function extractTouchScore(data) {
  if (!data) return 0;
  const raw =
    data.touch_target_score  ??
    data.touch_score         ??
    data.score               ??
    data.result?.score       ??
    0;
  return Math.max(0, Math.min(100, Number(raw) || 0));
}

/**
 * Derive recommendations from service responses and composite score.
 * @param {object} cogData
 * @param {object} salData
 * @param {object} touchData
 * @param {object} ahpResult
 * @returns {string[]}
 */
function buildRecommendations(cogData, salData, touchData, ahpResult) {
  const recs = [];

  const { breakdown } = ahpResult;

  if (breakdown.cognitive_load < 60) {
    recs.push('Reduce visual complexity — simplify the layout, limit information density.');
  }
  if (breakdown.visual_hierarchy < 60) {
    recs.push('Improve visual hierarchy — use size, colour, and contrast to guide user attention.');
  }
  if (breakdown.touch_target < 60) {
    recs.push('Increase touch-target sizes to at least 44 × 44 px to meet WCAG 2.5.5 guidelines.');
  }

  // Append service-level recommendations if available
  const appendServiceRecs = (data) => {
    if (!data) return;
    const svcRecs = data.recommendations || data.suggestions || [];
    if (Array.isArray(svcRecs)) {
      recs.push(...svcRecs.slice(0, 3)); // Max 3 per service
    }
  };
  appendServiceRecs(cogData);
  appendServiceRecs(salData);
  appendServiceRecs(touchData);

  return [...new Set(recs)]; // De-duplicate
}

/**
 * Count violations across service responses.
 */
function countViolations(cogData, salData, touchData) {
  let count = 0;
  const add = (data) => {
    if (!data) return;
    count += Number(data.violations_count || data.violation_count || data.violations?.length || 0);
  };
  add(cogData);
  add(salData);
  add(touchData);
  return count;
}

// ─── POST /api/analyze ────────────────────────────────────────────────────────
router.post(
  '/',
  authMiddleware,
  upload.single('image'), // optional image upload
  async (req, res) => {
    const traceId = uuidv4();
    let report    = null;

    try {
      // 1. Validate URL from body / multipart fields
      const parseResult = analyzeSchema.safeParse({
        url: req.body.url || req.body.URL
      });
      if (!parseResult.success) {
        return res.status(400).json({
          error:  'Validation failed.',
          issues: parseResult.error.flatten().fieldErrors
        });
      }

      const { url } = parseResult.data;

      // 2. Create a pending report so we can return traceId immediately
      report = await AuditReport.create({
        userId:  req.user.id,
        url,
        status:  'pending',
        traceId
      });

      // 3. Resolve image → base64
      let imageBase64 = null;

      if (req.file && req.file.buffer) {
        // User uploaded an image
        imageBase64 = req.file.buffer.toString('base64');
      } else {
        // Capture a screenshot of the provided URL
        console.info(`[analyze:${traceId}] No image supplied — capturing screenshot of ${url}`);
        imageBase64 = await captureScreenshot(url);

        if (!imageBase64) {
          console.warn(`[analyze:${traceId}] Screenshot capture unavailable — proceeding without image.`);
        }
      }

      // 4. Orchestrate microservice calls in parallel
      const { cognitive, touch, saliency, errors, analysisTime_ms } =
        await orchestrateAnalysis({ url, imageBase64, traceId });

      // 5. Extract numeric scores from service responses
      const scores = {
        cognitive_load:   extractCognitiveScore(cognitive),
        visual_hierarchy: extractSaliencyScore(saliency),
        touch_target:     extractTouchScore(touch)
      };

      // 6. AHP composite scoring
      const ahpResult = computeAHPScore(scores);

      // 7. Build ancillary fields
      const recommendations = buildRecommendations(cognitive, saliency, touch, ahpResult);
      const violations_count = countViolations(cognitive, saliency, touch);

      // 8. Persist completed report
      report.status          = errors.length === 3 ? 'failed' : 'completed';
      report.composite_score = ahpResult.composite_score;
      report.grade           = ahpResult.grade;
      report.scores          = scores;
      report.details         = { cognitive, saliency, touch };
      report.heatmap_base64  = saliency?.heatmap_base64 || null;
      report.violations_count = violations_count;
      report.recommendations  = recommendations;
      report.errors           = errors;
      report.analysisTime_ms  = analysisTime_ms;
      await report.save();

      // 9. Respond
      return res.status(200).json({
        traceId,
        reportId:        report._id.toString(),
        url,
        status:          report.status,
        composite_score: ahpResult.composite_score,
        grade:           ahpResult.grade,
        weights:         ahpResult.weights,
        consistency_ratio: ahpResult.consistency_ratio,
        scores,
        breakdown:       ahpResult.breakdown,
        details:         { cognitive, saliency, touch },
        heatmap_base64:  report.heatmap_base64,
        violations_count,
        recommendations,
        errors,
        analysisTime_ms
      });
    } catch (err) {
      console.error(`[analyze:${traceId}] Unhandled error:`, err.message);

      // Mark report as failed if it was created
      if (report) {
        try {
          report.status = 'failed';
          report.errors = [{ service: 'gateway', message: err.message }];
          await report.save();
        } catch { /* ignore secondary save error */ }
      }

      return res.status(500).json({
        error:   'Analysis failed due to an internal error.',
        traceId,
        details: err.message
      });
    }
  }
);

// ─── GET /api/analyze/status/:traceId ────────────────────────────────────────
router.get('/status/:traceId', authMiddleware, async (req, res) => {
  try {
    const { traceId } = req.params;

    const report = await AuditReport.findOne({
      traceId,
      userId: req.user.id      // Ownership check
    }).lean();

    if (!report) {
      return res.status(404).json({ error: 'No analysis found for the given trace ID.' });
    }

    return res.status(200).json({
      traceId:         report.traceId,
      reportId:        report._id.toString(),
      url:             report.url,
      status:          report.status,
      composite_score: report.composite_score,
      grade:           report.grade,
      scores:          report.scores,
      violations_count: report.violations_count,
      analysisTime_ms: report.analysisTime_ms,
      createdAt:       report.createdAt,
      errors:          report.errors
    });
  } catch (err) {
    console.error('[analyze/status]', err.message);
    return res.status(500).json({ error: 'Failed to retrieve analysis status.' });
  }
});

module.exports = router;
