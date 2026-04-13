# Hallucination Log - Current Status

## Day 3 Lab 1 Findings

| # | File | Area | Category | Issue | Required Fix | Current Status |
|---|------|------|----------|-------|--------------|----------------|
| 1 | `app/auth.py` | `logout` | Logic | Logout returned success when token not found | Raise error if token not found | Fixed |
| 2 | `app/auth.py` | `refresh` | Logic | Deleted token not committed before reuse | Add `db.commit()` after delete | Fixed |
| 3 | `app/auth.py` | `login` | API | Used `UserCreate` schema for login | Create separate `UserLogin` schema | Fixed |
| 4 | `app/auth.py` | `refresh` | Security | Token deletion not safely committed | Commit immediately after delete | Fixed |
| 5 | `app/auth.py` | `/me` | Logic | No inactive-user validation | Add `is_active` check | Fixed |
| 6 | `app/auth.py` | `logout`/`refresh` | Security | No token ownership/binding validation | Validate token ownership/user binding | Fixed |
| 7 | `app/auth.py` | `logout` | API | Missing response model | Add response schema | Fixed |

## Day 3 - Lab 2 Hunt Findings

| # | File | Category | Finding | Why It Matters | Severity | Current Status |
|---|------|----------|---------|----------------|----------|----------------|
| 1 | `app/auth.py` | API/Library | bcrypt usage concern | Preferred FastAPI pattern is passlib context usage | Medium | Fixed (using `passlib` context) |
| 2 | `app/dependencies.py` | Logic | Token type not validated | Refresh/invalid token could be accepted as access token | High | Fixed |
| 3 | `app/schemas.py` | Security | No password validation | Weak passwords could be accepted | High | Fixed |
| 4 | `app/models.py` + `app/auth.py` | Security | Refresh token stored as plain value | DB leak could expose active refresh tokens | High | Fixed (stored as hash) |
| 5 | `app/config.py` | Security | Hardcoded `SECRET_KEY` | Secret exposure risk | High | Fixed (no hardcoded literal secret) |

## Notes

- Missing token binding: fixed by validating token type for access tokens and binding refresh-token operations to the correct user.
- No rate limiting: not implemented in this lab code yet (outside the listed fixed items above).