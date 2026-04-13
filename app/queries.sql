-- PostgreSQL query to fetch active users with their latest refresh tokens
-- Includes multiple joins, filtering, ordering, and pagination

SELECT 
    u.id AS user_id, 
    u.email, 
    u.is_active, 
    rt.token AS refresh_token, 
    rt.expires_at AS token_expiry,
    rt.created_at AS token_created_at
FROM 
    users u
JOIN 
    refresh_tokens rt ON u.id = rt.user_id
-- Example filtering: only active users whose tokens have not expired
WHERE 
    u.is_active = TRUE 
    AND rt.expires_at > NOW()
    AND u.email LIKE '%@example.com'
-- Ordering by user creation date and then token creation date
ORDER BY 
    u.created_at DESC, 
    rt.created_at DESC
-- Pagination: Limit to 10 results per page, starting from the second page (offset 10)
LIMIT 10 OFFSET 10;
