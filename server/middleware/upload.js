'use strict';

const multer = require('multer');

// Keep files in memory as Buffers — no temp files on disk
const storage = multer.memoryStorage();

/**
 * Allow only web-safe image formats.
 * @param {import('express').Request} _req
 * @param {Express.Multer.File} file
 * @param {Function} cb
 */
function fileFilter(_req, file, cb) {
  const ALLOWED_MIME_TYPES = ['image/png', 'image/jpeg', 'image/webp'];

  if (ALLOWED_MIME_TYPES.includes(file.mimetype)) {
    cb(null, true);
  } else {
    cb(
      Object.assign(new Error('Invalid file type. Only PNG, JPEG, and WebP images are accepted.'), {
        status: 400
      }),
      false
    );
  }
}

/**
 * Multer instance pre-configured for screenshot uploads.
 * Usage in routes:
 *   router.post('/analyze', upload.single('image'), handler);
 */
const upload = multer({
  storage,
  fileFilter,
  limits: {
    fileSize: 20 * 1024 * 1024, // 20 MB
    files: 1
  }
});

module.exports = { upload };
