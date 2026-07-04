'use strict';

/**
 * orchestrator.js
 * ───────────────
 * Parallel microservice orchestrator using circuit breakers (opossum).
 * Uses Promise.allSettled — partial results are returned even when
 * individual services fail or trip their circuit breaker.
 */

const axios          = require('axios');
const CircuitBreaker = require('opossum');

// ─── Service base URLs ────────────────────────────────────────────────────────
const SERVICES = {
  cognitive: process.env.COGNITIVE_URL || 'http://localhost:8001',
  touch:     process.env.TOUCH_URL     || 'http://localhost:8002',
  saliency:  process.env.SALIENCY_URL  || 'http://localhost:8003'
};

const TIMEOUT = parseInt(process.env.SERVICE_TIMEOUT_MS, 10) || 60_000;

// ─── Circuit-breaker options ──────────────────────────────────────────────────
const CB_OPTIONS = {
  timeout:                  TIMEOUT, // Max ms before treating as failure
  errorThresholdPercentage: 50,      // Open CB after 50 % failures
  resetTimeout:             30_000,  // ms before attempting half-open
  volumeThreshold:          3        // Min calls before CB stats count
};

// ─── Raw service callers ──────────────────────────────────────────────────────

/**
 * Call the Cognitive Load microservice.
 * @param {{ imageBase64: string, traceId: string }} params
 */
async function callCognitive({ imageBase64, traceId }) {
  const response = await axios.post(
    `${SERVICES.cognitive}/analyze`,
    { image_base64: imageBase64 },
    {
      timeout: TIMEOUT,
      headers: { 'Content-Type': 'application/json', 'X-Trace-Id': traceId }
    }
  );
  return response.data;
}

/**
 * Call the Touch Target microservice.
 * @param {{ url: string, traceId: string }} params
 */
async function callTouch({ url, traceId }) {
  const response = await axios.post(
    `${SERVICES.touch}/analyze`,
    { url },
    {
      timeout: TIMEOUT,
      headers: { 'Content-Type': 'application/json', 'X-Trace-Id': traceId }
    }
  );
  return response.data;
}

/**
 * Call the Visual Saliency / Visual Hierarchy microservice.
 * @param {{ imageBase64: string, traceId: string }} params
 */
async function callSaliency({ imageBase64, traceId }) {
  const response = await axios.post(
    `${SERVICES.saliency}/analyze`,
    { image_base64: imageBase64 },
    {
      timeout: TIMEOUT,
      headers: { 'Content-Type': 'application/json', 'X-Trace-Id': traceId }
    }
  );
  return response.data;
}

// ─── Circuit breakers ─────────────────────────────────────────────────────────
const cognitiveBreaker = new CircuitBreaker(callCognitive, CB_OPTIONS);
const touchBreaker     = new CircuitBreaker(callTouch,     CB_OPTIONS);
NS);

// Log CB state changes
[
  { name: 'cognitive-load',    cb: cognitiveBreaker },
  { name: 'touch-target',      cb: touchBreaker     },
  { name: 'visual-saliency',   cb: saliencyBreaker  }
].forEach(({ name, cb }) => {
  cb.on('open',     () => console.warn(`[CircuitBreaker:${name}] OPEN — requests short-circuited`));
  cb.on('halfOpen', () => console.info(`[CircuitBreaker:${name}] HALF-OPEN — testing recovery`));
  cb.on('close',    () => console.info(`[CircuitBreaker:${name}] CLOSED — service recovered`));
  cb.on('fallback', () => console.warn(`[CircuitBreaker:${name}] Fallback triggered`));
});

// ─── Orchestrator ─────────────────────────────────────────────────────────────

/**
 * Fire all three microservice calls in parallel.
 * Uses Promise.allSettled — never throws; always returns a result object.
 *
 * @param {{ url: string, imageBase64: string, traceId: string }} params
 * @returns {Promise<{
 *   cognitive:       object|null,
 *   touch:           object|null,
 *   saliency:        object|null,
 *   errors:          Array<{service:string, message:string}>,
 *   analysisTime_ms: number
 * }>}
 */
async function orchestrateAnalysis({ url, imageBase64, traceId }) {
  const startTime = Date.now();

  const [cogResult, touchResult, salResult] = await Promise.allSettled([
    cognitiveBreaker.fire({ imageBase64, traceId }),
    touchBreaker.fire({ url, traceId }),
    saliencyBreaker.fire({ imageBase64, traceId })
  ]);

  /** @param {PromiseSettledResult} settled */
  const extractData  = (settled) => (settled.status === 'fulfilled' ? settled.value : null);

  /**
   * @param {PromiseSettledResult} settled
   * @param {string} serviceName
   */
  const extractError = (settled, serviceName) =>
    settled.status === 'rejected'
      ? { service: serviceName, message: settled.reason?.message || 'Unknown error' }
      : null;

  const cogData  = extractData(cogResult);
  const touchData = extractData(touchResult);
  const salData  = extractData(salResult);

  const errors = [
    extractError(cogResult,  'cognitive-load'),
    extractError(touchResult, 'touch-target'),
    extractError(salResult,  'visual-hierarchy')
  ].filter(Boolean);

  if (errors.length) {
    console.warn('[orchestrator] Some services failed:', errors.map(e => `${e.service}: ${e.message}`).join(' | '));
  }

  return {
    cognitive:       cogData,
    touch:           touchData,
    saliency:        salData,
    errors,
    analysisTime_ms: Date.now() - startTime
  };
}

module.exports = { orchestrateAnalysis, SERVICES };
