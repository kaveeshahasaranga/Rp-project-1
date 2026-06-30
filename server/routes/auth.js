'use strict';

const express = require('express');
const jwt     = require('jsonwebtoken');
const { z }   = require('zod');

const User           = require('../models/User');
const authMiddleware = require('../middleware/auth');

const router     = express.Router();
const JWT_SECRET  = process.env.JWT_SECRET     || 'dev-secret-change-in-production';
const JWT_EXPIRES = process.env.JWT_EXPIRES_IN || '7d';

// ─── Helpers ──────────────────────────────────────────────────────────────────

/**
 * Issue a signed JWT for the given user document.
 * @param {import('mongoose').Document} user
 * @returns {string}
 */
function issueToken(user) {
  return jwt.sign(
    { id: user._id.toString(), email: user.email, role: user.role },
    JWT_SECRET,
    { expiresIn: JWT_EXPIRES }
  );
}

/**
 * Return a safe public projection of the user document (no password).
 * @param {import('mongoose').Document} user
 */
function safeUser(user) {
  return { id: user._id.toString(), name: user.name, email: user.email, role: user.role };
}

// ─── Validation schemas ───────────────────────────────────────────────────────
const registerSchema = z.object({
  name:     z.string().min(2,  'Name must be at least 2 characters.').max(100),
  email:    z.string().email('Please provide a valid email address.'),
  password: z.string().min(8,  'Password must be at least 8 characters.')
});

const loginSchema = z.object({
  email:    z.string().email('Please provide a valid email address.'),
  password: z.string().min(1,  'Password is required.')
});

// ─── POST /api/auth/register ──────────────────────────────────────────────────
router.post('/register', async (req, res) => {
  try {
    // 1. Validate input
    const parseResult = registerSchema.safeParse(req.body);
    if (!parseResult.success) {
      return res.status(400).json({
        error:  'Validation failed.',
        issues: parseResult.error.flatten().fieldErrors
      });
    }

    const { name, email, password } = parseResult.data;

    // 2. Check for duplicate email
    const existing = await User.findOne({ email: email.toLowerCase().trim() });
    if (existing) {
      return res.status(409).json({ error: 'An account with that email already exists.' });
    }

    // 3. Create user (password hashed by pre-save hook)
    const user  = await User.create({ name, email, password });

    // 4. Issue JWT
    const token = issueToken(user);

    return res.status(201).json({
      message: 'Account created successfully.',
      token,
      user: safeUser(user)
    });
  } catch (err) {
    console.error('[Auth/register]', err.message);
    return res.status(500).json({ error: 'Registration failed. Please try again.' });
  }
});

// ─── POST /api/auth/login ─────────────────────────────────────────────────────
router.post('/login', async (req, res) => {
  try {
    // 1. Validate input
    const parseResult = loginSchema.safeParse(req.body);
    if (!parseResult.success) {
      return res.status(400).json({
        error:  'Validation failed.',
        issues: parseResult.error.flatten().fieldErrors
      });
    }

    const { email, password } = parseResult.data;

    // 2. Look up user (re-select password field)
    const user = await User.findByEmail(email);
    if (!user) {
      // Generic message — don't reveal whether email exists
      return res.status(401).json({ error: 'Invalid email or password.' });
    }

    // 3. Verify password
    const match = await user.comparePassword(password);
    if (!match) {
      return res.status(401).json({ error: 'Invalid email or password.' });
    }

    // 4. Issue JWT
    const token = issueToken(user);

    return res.status(200).json({
      message: 'Login successful.',
      token,
      user: safeUser(user)
    });
  } catch (err) {
    console.error('[Auth/login]', err.message);
    return res.status(500).json({ error: 'Login failed. Please try again.' });
  }
});

// ─── GET /api/auth/me ─────────────────────────────────────────────────────────
router.get('/me', authMiddleware, async (req, res) => {
  try {
    const user = await User.findById(req.user.id).lean();
    if (!user) {
      return res.status(404).json({ error: 'User account not found.' });
    }

    return res.status(200).json({
      user: {
        id:        user._id.toString(),
        name:      user.name,
        email:     user.email,
        role:      user.role,
        createdAt: user.createdAt
      }
    });
  } catch (err) {
    console.error('[Auth/me]', err.message);
    return res.status(500).json({ error: 'Failed to retrieve user information.' });
  }
});

module.exports = router;
