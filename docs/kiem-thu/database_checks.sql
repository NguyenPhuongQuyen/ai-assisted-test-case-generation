-- Week 05 database verification queries. Run in pgAdmin Query Tool or psql.
SELECT id, email, role, failed_login_attempts, locked_until, created_at
FROM users
ORDER BY id;

SELECT id, name, parent_id, created_by, created_at
FROM modules
ORDER BY id;

SELECT id, module_id, created_by, LEFT(content, 100) AS content_preview, created_at
FROM requirements
ORDER BY id DESC;

SELECT id, requirement_id, module_id, summary, priority, status, created_by, created_at
FROM test_cases
ORDER BY id DESC;

SELECT id, user_id, action, entity_type, entity_id, after_state, created_at
FROM audit_logs
ORDER BY id DESC;
