'use strict';

require('dotenv').config();

const express = require('express');
const mongoose = require('mongoose');
const helmet = require('helmet');
const cors = require('cors');
const morgan = require('morgan');
const rateLimit = require('express-rate-limit');

// ─── Route imports ────────────────────────────────────────────────────────────
const authRoutes    = require('./routes/auth');
const analyzeRoutes = require('./routes/analyze');
const reportsRoutes = require('./routes/reports');

const app  = express();
const PORT = process.env.PORT || 5000;

// ─── Security & request middleware ────────────────────────────────────────────
app.use(helmet());

app.use(cors({
  origin: process.env.CLIENT_URL || 'http://localhost:3000',
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Trace-Id']
}));

app.use(morgan('dev'));

app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// ─── Rate limiting ────────────────────────────────────────────────────────────
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100,
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'Too many requests, please try again after 15 minutes.' }
});
app.use(limiter);

// ─── Health check (bypasses auth / rate limiting) ─────────────────────────────
app.get('/health', (_req, res) =>
  res.json({ status: 'ok', timestamp: new Date().toISOString() })
);

// ─── API routes ───────────────────────────────────────────────────────────────
app.use('/api/auth',    authRoutes);
app.use('/api/analyze', analyzeRoutes);
app.use('/api/reports', reportsRoutes);

// ─── 404 handler ─────────────────────────────────────────────────────────────
app.use((_req, res) => {
  res.status(404).json({ error: 'Route not found.' });
});

// ─── Global error handler ─────────────────────────────────────────────────────
// eslint-disable-next-line no-unused-vars
app.use((err, _req, res, _next) => {
  console.error('[ERROR]', err.stack || err.message);
  const status  = err.status || err.statusCode || 500;
  const message = err.message || 'Internal server error';
  res.status(status).json({ error: message });
});

// ─── MongoDB connection with retry ────────────────────────────────────────────
const MONGO_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/ux-analyzer';
const MAX_RETRIES = 5;
const RETRY_DELAY_MS = 3000;

async function connectWithRetry(attempt = 1) {
  try {
    await mongoose.connect(MONGO_URI, {
      serverSelectionTimeoutMS: 5000,
      socketTimeoutMS: 45000
    });
    console.log(`[MongoDB] Connected → ${MONGO_URI}`);
  } catch (err) {
    if (attempt < MAX_RETRIES) {
      console.warn(`[MongoDB] Connection failed (attempt ${attempt}/${MAX_RETRIES}). Retrying in ${RETRY_DELAY_MS / 1000}s…`);
      await new Promise(resolve => setTimeout(resolve, RETRY_DELAY_MS));
      return connectWithRetry(attempt + 1);
    }
    console.error('[MongoDB] Could not connect after maximum retries. Exiting.');
    process.exit(1);
  }
}

// ─── Boot ─────────────────────────────────────────────────────────────────────
(async () => {
  await connectWithRetry();

  app.listen(PORT, () => {
    console.log('╔══════════════════════════════════════════════════╗');
    console.log(`║   UX Analyzer API Gateway — port ${PORT}           ║`);
    console.log(`║   ENV        : ${(process.env.NODE_ENV || 'development').padEnd(32)}║`);
    console.log(`║   MongoDB    : ${MONGO_URI.slice(0, 32).padEnd(32)}║`);
    console.log(`║   CORS origin: ${(process.env.CLIENT_URL || 'http://localhost:3000').padEnd(32)}║`);
    console.log('╚══════════════════════════════════════════════════╝');
  });
})();

module.exports = app; // for testing
