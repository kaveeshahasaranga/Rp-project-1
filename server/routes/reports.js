'use strict';

const express = require('express');
const mongoose = require('mongoose');

const authMiddleware = require('../middleware/auth');
const AuditReport    = require('../models/AuditReport');

const router = express.Router();

// All routes in this file require a valid JWT
router.use(authMiddleware);

// ─── GET /api/reports ─────────────────────────────────────────────────────────
/**
 * List all audit reports belonging to the authenticated user.
 * Returns a lightweight summary array (no heavy heatmap_base64 or details).
 */
router.get('/', async (req, res) => {
  try {
    const reports = await AuditReport.find({ userId: req.user.id })
      .sort({ createdAt: -1 })
      .select('-heatmap_base64 -details') // Omit heavy fields from list view
      .lean();

    return res.status(200).json({
      count:   reports.length,
      reports: reports.map(r => ({
        id:              r._id.toString(),
        url:             r.url,
        status:          r.status,
        composite_score: r.composite_score,
        grade:           r.grade,
        scores:          r.scores,
        violations_count: r.violations_count,
        traceId:         r.traceId,
        analysisTime_ms: r.analysisTime_ms,
        errors:          r.errors,
        createdAt:       r.createdAt
      }))
    });
  } catch (err) {
    console.error('[reports/list]', err.message);
    return res.status(500).json({ error: 'Failed to retrieve reports.' });
  }
});

// ─── GET /api/reports/:id ─────────────────────────────────────────────────────
/**
 * Retrieve a single full audit report by MongoDB ObjectId.
 * Only accessible by the report's owner.
 */
router.get('/:id', async (req, res) => {
  try {
    const { id } = req.params;

    // Validate ObjectId format before hitting the DB
    if (!mongoose.Types.ObjectId.isValid(id)) {
      return res.status(400).json({ error: 'Invalid report ID format.' });
    }

    const report = await AuditReport.findOne({
      _id:    id,
      userId: req.user.id   // Ownership check — prevent IDOR
    }).lean();

    if (!report) {
      return res.status(404).json({ error: 'Report not found or access denied.' });
    }

    return res.status(200).json({
      id:              report._id.toString(),
      userId:          report.userId.toString(),
      url:             report.url,
      status:          report.status,
      composite_score: report.composite_score,
      grade:           report.grade,
      scores:          report.scores,
      details:         report.details,
      heatmap_base64:  report.heatmap_base64,
      violations_count: report.violations_count,
      recommendations: report.recommendations,
      errors:          report.errors,
      traceId:         report.traceId,
      analysisTime_ms: report.analysisTime_ms,
      createdAt:       report.createdAt
    });
  } catch (err) {
    console.error('[reports/get]', err.message);
    return res.status(500).json({ error: 'Failed to retrieve report.' });
  }
});

// ─── DELETE /api/reports/:id ──────────────────────────────────────────────────
/**
 * Permanently delete a report owned by the authenticated user.
 */
router.delete('/:id', async (req, res) => {
  try {
    const { id } = req.params;

    if (!mongoose.Types.ObjectId.isValid(id)) {
      return res.status(400).json({ error: 'Invalid report ID format.' });
    }

    const deleted = await AuditReport.findOneAndDelete({
      _id:    id,
      userId: req.user.id  // Ownership check
    });

    if (!deleted) {
      return res.status(404).json({ error: 'Report not found or access denied.' });
    }

    return res.status(200).json({
      message:  'Report deleted successfully.',
      reportId: deleted._id.toString()
    });
  } catch (err) {
    console.error('[reports/delete]', err.message);
    return res.status(500).json({ error: 'Failed to delete report.' });
  }
});

module.exports = router;
