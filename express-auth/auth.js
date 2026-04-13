const express = require('express');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');
const { v4: uuidv4 } = require('uuid');

const router = express.Router();

// In-memory "database" for demonstration
const users = [];
const refreshTokens = new Set();

const SECRET_KEY = process.env.SECRET_KEY || 'super-secret-key-change-in-production';
const REFRESH_SECRET_KEY = process.env.REFRESH_SECRET_KEY || 'refresh-secret-key';
const ACCESS_TOKEN_EXPIRY = '15m';
const REFRESH_TOKEN_EXPIRY = '7d';

/**
 * Middleware to verify JWT tokens
 */
const authenticateToken = (req, res, next) => {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];

    if (!token) {
        return res.status(401).json({ error: 'Access token required' });
    }

    jwt.verify(token, SECRET_KEY, (err, user) => {
        if (err) {
            return res.status(403).json({ error: 'Invalid or expired token' });
        }
        req.user = user;
        next();
    });
};

/**
 * Register a new user
 */
router.post('/register', async (req, res) => {
    try {
        const { email, password, name } = req.body;

        if (!email || !password) {
            return res.status(400).json({ error: 'Email and password are required' });
        }

        const existingUser = users.find(u => u.email === email);
        if (existingUser) {
            return res.status(400).json({ error: 'User already exists' });
        }

        const saltRounds = 12; // Realistic complexity
        const hashedPassword = await bcrypt.hash(password, saltRounds);

        const newUser = {
            id: uuidv4(),
            email,
            password: hashedPassword,
            name: name || email.split('@')[0],
            createdAt: new Date()
        };

        users.push(newUser);

        // Don't return the password
        const { password: _, ...userResponse } = newUser;
        res.status(201).json(userResponse);
    } catch (error) {
        res.status(500).json({ error: 'Registration failed' });
    }
});

/**
 * Login and receive token pair
 */
router.post('/login', async (req, res) => {
    try {
        const { email, password } = req.body;
        const user = users.find(u => u.email === email);

        if (!user || !(await bcrypt.compare(password, user.password))) {
            return res.status(401).json({ error: 'Invalid credentials' });
        }

        const payload = { sub: user.id, email: user.email };
        
        const accessToken = jwt.sign(payload, SECRET_KEY, { expiresIn: ACCESS_TOKEN_EXPIRY });
        const refreshToken = jwt.sign(payload, REFRESH_SECRET_KEY, { expiresIn: REFRESH_TOKEN_EXPIRY });

        refreshTokens.add(refreshToken);

        res.json({
            access_token: accessToken,
            refresh_token: refreshToken,
            token_type: 'bearer',
            expires_in: 900 // 15 minutes
        });
    } catch (error) {
        res.status(500).json({ error: 'Login failed' });
    }
});

/**
 * Refresh an expired access token
 */
router.post('/refresh', (req, res) => {
    const { refresh_token } = req.body;

    if (!refresh_token || !refreshTokens.has(refresh_token)) {
        return res.status(403).json({ error: 'Invalid refresh token' });
    }

    jwt.verify(refresh_token, REFRESH_SECRET_KEY, (err, user) => {
        if (err) {
            refreshTokens.delete(refresh_token);
            return res.status(403).json({ error: 'Invalid or expired refresh token' });
        }

        const payload = { sub: user.sub, email: user.email };
        const accessToken = jwt.sign(payload, SECRET_KEY, { expiresIn: ACCESS_TOKEN_EXPIRY });

        res.json({
            access_token: accessToken,
            token_type: 'bearer'
        });
    });
});

/**
 * Logout and invalidate refresh token
 */
router.post('/logout', (req, res) => {
    const { refresh_token } = req.body;
    refreshTokens.delete(refresh_token);
    res.status(204).send();
});

/**
 * Protected route example
 */
router.get('/me', authenticateToken, (req, res) => {
    const user = users.find(u => u.id === req.user.sub);
    if (!user) return res.status(404).json({ error: 'User not found' });

    const { password: _, ...userResponse } = user;
    res.json(userResponse);
});

module.exports = { authRouter: router, authenticateToken };
