# Personal Security Review Checklist
 
*AI Developer Bootcamp — Day 5  |  Your Name: Ayush Rathour  |  Date: 2026-04-13*
 
---
 
## How to Use This Checklist
 
Review every item before merging AI-generated code to your main branch.

Mark completed items with `[x]`. Leave incomplete items as `[ ]`.

Items marked **(CRITICAL)** must pass before any deployment.
 
---
 
## Foundation Items (OWASP + Bootcamp)
 
### Secrets and Credentials

- [ ] No hardcoded secrets, API keys, or passwords in any source file **(CRITICAL)**

- [ ] Passwords hashed with bcrypt — never stored as plaintext **(CRITICAL)**
 
### Authentication and Authorisation

- [ ] JWT expiry set appropriately (access tokens: max 15-60 minutes; refresh tokens: max 7 days)

- [ ] Authentication dependency applied to every route that requires it **(CRITICAL)**

- [ ] Login endpoint returns the same error for wrong email and wrong password

      (prevents user enumeration — error must say 'Invalid credentials', nothing more)
 
### Input and Data

- [ ] All user inputs validated before use (type, range, length, format)

- [ ] SQL queries use parameterised statements — no f-strings or string concatenation **(CRITICAL)**

- [ ] API response schemas are explicit — no database model returned directly

      (response schema must exclude hashed_password, is_admin, internal fields)
 
### Configuration and Operations

- [ ] CORS configured correctly — no wildcard (*) allowed in production

- [ ] Rate limiting applied to all authentication endpoints
 
---
 
## My Personal Items

*(Add 3 items based on what YOU found during this week)*
 
- [ ] Verify db.commit() and db.refresh() are both called after every db.add() so data is actually saved properly

- [ ] Convert JWT payload user ID (sub) to int before using it in database queries to avoid type mismatch issues

- [ ] Ensure old refresh tokens are deleted during refresh and logout so tokens cannot be reused
 
 
---
 
## Notes
 
*Add any project-specific notes here as you use this checklist.*
 