'use strict';

const mongoose = require('mongoose');

// ─── Sub-schemas ──────────────────────────────────────────────────────────────
const scoresSchema = new mongoose.Schema(
  {
    cognitive_load:   { type: Number, min: 0, max: 100 },
    visual_hierarchy: { type: Number, min: 0, max: 100 },
    touch_target:     { type: Number, min: 0, max: 100 }
  },
  { _id: false }
);

const errorSchema = new mongoose.Schema(
  {
    service: { type: String, required: true },
    message: { type: String, required: true }
  },
  { _id: false }
);

// ─── Main schema ──────────────────────────────────────────────────────────────
const auditReportSchema = new mongoose.Schema(
  {
    userId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
      required: [true, 'User ID is required.'],
      index: true
    },
    url: {
      type: String,
      required: [true, 'Target URL is required.'],
      trim: true
    },
    status: {
      type: String,
      enum: ['pending', 'completed', 'failed'],
      default: 'pending'
    },
    composite_score: {
      type: Number,
      min: 0,
      max: 100
    },
    grade: {
      type: String,
      enum: ['A', 'B', 'C', 'D', 'F']
    },
    scores: {
      type: scoresSchema,
      default: () => ({})
    },
    details: {
      cognitive: { type: mongoose.Schema.Types.Mixed, default: null },
      saliency:  { type: mongoose.Schema.Types.Mixed, default: null },
      touch:     { type: mongoose.Schema.Types.Mixed, default: null }
    },
    heatmap_base64: {
      type: String,
      default: null
    },
    violations_count: {
      type: Number,
      default: 0
    },
    recommendations: {
      type: [String],
      default: []
    },
    errors: {
      type: [errorSchema],
      default: []
    },
    traceId: {
      type: String,
      index: true
    },
    analysisTime_ms: {
      type: Number
    },
    createdAt: {
      type: Date,
      default: Date.now,
      index: true
    }
  },
  {
    versionKey: false
  }
);

// ─── Virtual: compute grade from composite_score ───────────────────────────────
auditReportSchema.virtual('gradeFromScore').get(function computeGrade() {
  const s = this.composite_score;
  if (s == null) return null;
  if (s >= 90) return 'A';
  if (s >= 75) return 'B';
  if (s >= 55) return 'C';
  if (s >= 35) return 'D';
  return 'F';
});

// ─── Static method ────────────────────────────────────────────────────────────

/**
 * Retrieve all reports for a given user, newest first.
 * @param {string|import('mongoose').Types.ObjectId} userId
 * @returns {Promise<import('mongoose').Document[]>}
 */
auditReportSchema.statics.findByUser = function findByUser(userId) {
  return this.find({ userId }).sort({ createdAt: -1 }).lean();
};

const AuditReport = mongoose.model('AuditReport', auditReportSchema);

module.exports = AuditReport;
