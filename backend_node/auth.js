// Hostel 360 - Authentication & Password Utilities
// Uses Node 24 native crypto module
const crypto = require('node:crypto');

const SECRET_KEY = process.env.HOSTEL360_SECRET_KEY || 'hostel360-super-secret-jwt-signing-key-2026-srm';

function hashPassword(password) {
  const salt = crypto.randomBytes(16).toString('hex');
  const hash = crypto.pbkdf2Sync(password, salt, 100000, 32, 'sha256').toString('hex');
  return `${salt}$${hash}`;
}

function verifyPassword(plainPassword, storedHash) {
  try {
    if (!storedHash || !storedHash.includes('$')) return false;
    const [salt, originalHash] = storedHash.split('$');
    const testHash = crypto.pbkdf2Sync(plainPassword, salt, 100000, 32, 'sha256').toString('hex');
    return crypto.timingSafeEqual(Buffer.from(testHash, 'utf-8'), Buffer.from(originalHash, 'utf-8'));
  } catch (e) {
    return false;
  }
}

function createToken(payload, expiresInSeconds = 86400) {
  const header = { alg: 'HS256', typ: 'JWT' };
  const now = Math.floor(Date.now() / 1000);
  const fullPayload = { ...payload, iat: now, exp: now + expiresInSeconds };

  const encodeB64 = (obj) => Buffer.from(JSON.stringify(obj)).toString('base64url');
  const tokenHead = `${encodeB64(header)}.${encodeB64(fullPayload)}`;
  const signature = crypto.createHmac('sha256', SECRET_KEY).update(tokenHead).digest('base64url');

  return `${tokenHead}.${signature}`;
}

function verifyToken(token) {
  try {
    if (!token) return null;
    const parts = token.split('.');
    if (parts.length !== 3) return null;

    const [headerB64, payloadB64, signature] = parts;
    const expectedSig = crypto.createHmac('sha256', SECRET_KEY).update(`${headerB64}.${payloadB64}`).digest('base64url');

    if (signature !== expectedSig) return null;

    const payload = JSON.parse(Buffer.from(payloadB64, 'base64url').toString('utf-8'));
    const now = Math.floor(Date.now() / 1000);
    if (payload.exp && now > payload.exp) return null;

    return payload;
  } catch (e) {
    return null;
  }
}

module.exports = {
  SECRET_KEY,
  hashPassword,
  verifyPassword,
  createToken,
  verifyToken
};
