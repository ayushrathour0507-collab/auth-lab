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
 