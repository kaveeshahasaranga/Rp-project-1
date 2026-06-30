'use strict';

/**
 * screenshotter.js
 * ────────────────
 * Headless browser screenshot capture using puppeteer-core.
 * Falls back gracefully if puppeteer-core is not installed or
 * no compatible Chrome executable can be found.
 */

const { execSync } = require('child_process');

const VIEWPORT = { width: 1440, height: 900 };
const TIMEOUT_MS = 30_000;

/**
 * Attempt to locate an installed Chrome / Chromium executable on the host.
 * Returns the first path that exists, or null.
 * @returns {string|null}
 */
function findChromePath() {
  const candidates = [
    // macOS
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    // Linux
    '/usr/bin/google-chrome',
    '/usr/bin/google-chrome-stable',
    '/usr/bin/chromium-browser',
    '/usr/bin/chromium',
    '/snap/bin/chromium',
    // Windows (only reached on Windows hosts)
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe'
  ];

  const fs = require('fs');
  for (const p of candidates) {
    try {
      if (fs.existsSync(p)) return p;
    } catch {
      // ignore
    }
  }

  // Last resort: ask the shell
  for (const cmd of ['which google-chrome', 'which chromium-browser', 'which chromium']) {
    try {
      const result = execSync(cmd, { stdio: ['pipe', 'pipe', 'pipe'] }).toString().trim();
      if (result) return result;
    } catch {
      // ignore
    }
  }

  return null;
}

/**
 * Capture a full-page screenshot of the given URL.
 *
 * @param {string} url  A fully-qualified URL (https://…)
 * @returns {Promise<string|null>}  PNG image as a base64-encoded string,
 *                                  or null if capture is unavailable.
 */
async function captureScreenshot(url) {
  let puppeteer;

  // ── Gracefully handle missing puppeteer-core ─────────────────────────────
  try {
    puppeteer = require('puppeteer-core');
  } catch {
    console.warn('[screenshotter] puppeteer-core not found — screenshot capture unavailable.');
    return null;
  }

  const executablePath = findChromePath();
  if (!executablePath) {
    console.warn('[screenshotter] No Chrome/Chromium executable found — screenshot capture unavailable.');
    return null;
  }

  let browser = null;
  try {
    browser = await puppeteer.launch({
      executablePath,
      headless: 'new',
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--window-size=1440,900'
      ],
      timeout: TIMEOUT_MS
    });

    const page = await browser.newPage();

    await page.setViewport(VIEWPORT);

    // Block ads/trackers to speed up load
    await page.setRequestInterception(true);
    page.on('request', (req) => {
      const resourceType = req.resourceType();
      if (['media', 'font', 'websocket'].includes(resourceType)) {
        req.abort();
      } else {
        req.continue();
      }
    });

    await page.goto(url, {
      waitUntil: 'networkidle2',
      timeout:   TIMEOUT_MS
    });

    const screenshotBuffer = await page.screenshot({
      type:     'png',
      fullPage: false // viewport-only, consistent 1440×900
    });

    return screenshotBuffer.toString('base64');
  } catch (err) {
    console.error('[screenshotter] Screenshot capture failed:', err.message);
    return null;
  } finally {
    if (browser) {
      await browser.close().catch(() => {});
    }
  }
}

module.exports = { captureScreenshot };
