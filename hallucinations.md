# Hallucination Log
 
| # | File | Line | Category | Issue | Fix |

|---|------|------|----------|-------|-----|

| 1 | app/auth.py | logout | Logic | Logout returns success even if token not found | Raise error if token not found |

| 2 | app/auth.py | refresh | Logic | Deleted token not committed before reuse | Add db.commit() after delete |

| 3 | app/auth.py | login | API | Using UserCreate schema for login | Create separate UserLogin schema |

| 4 | app/auth.py | refresh | Security | Token deletion not safely committed | Commit immediately |

| 5 | app/auth.py | /me | Logic | No check for inactive user | Add is_active validation |

| 6 | app/auth.py | logout/refresh | Security | No token ownership validation | Check user_id |

| 7 | app/auth.py | logout | API | Missing response model | Add response schema |
 

 
## Day 3 — Lab 2: Hunt Lab Findings
 
| # | File | Category | What AI Did | Why It's Wrong | Severity |
|---|------|----------|------------|---------------|----------|
| 1 | auth.py | API/Library | Used bcrypt instead of passlib | Not standard FastAPI pattern | Medium |
| 2 | dependencies.py | Logic | Did not validate token type | Refresh tokens could be misused | High |
| 3 | schemas.py | Security | No password validation | Weak passwords allowed | High |
| 4 | models.py | Security | Stored refresh token as plain string | Token leakage risk | High |
| 5 | config.py | Security | Hardcoded SECRET_KEY | Sensitive data exposed | High |


### Gemini vs Manual Comparison

**Issues Gemini found that I missed:**
- Missing token binding
- No rate limiting
**Issues I found manually:**
- bcrypt instead of passlib usage
**Most surprising finding:**
- Hardcoded SECRET_KEY is a major security risk