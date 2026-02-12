-- STORY-202 DB-M06: RPC to get conversations with unread count in single query
-- Eliminates N+1 query pattern in backend/routes/messages.py lines 112-122

CREATE OR REPLACE FUNCTION get_conversations_with_unread_count(
    p_user_id UUID,
    p_is_admin BOOLEAN DEFAULT FALSE,
    p_status TEXT DEFAULT NULL,
    p_limit INT DEFAULT 50,
    p_offset INT DEFAULT 0
)
RETURNS TABLE (
    id UUID,
    user_id UUID,
    user_email TEXT,
    subject TEXT,
    category TEXT,
    status TEXT,
    last_message_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ,
    unread_count BIGINT,
    total_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    WITH filtered_conversations AS (
        SELECT c.*,
            p.email as profile_email,
            COUNT(*) OVER() as total
        FROM conversations c
        LEFT JOIN profiles p ON p.id = c.user_id
        WHERE (p_is_admin OR c.user_id = p_user_id)
            AND (p_status IS NULL OR c.status = p_status)
        ORDER BY c.last_message_at DESC
        LIMIT p_limit OFFSET p_offset
    )
    SELECT
        fc.id,
        fc.user_id,
        CASE WHEN p_is_admin THEN fc.profile_email ELSE NULL END,
        fc.subject,
        fc.category,
        fc.status,
        fc.last_message_at,
        fc.created_at,
        COALESCE(
            (SELECT COUNT(*) FROM messages m
             WHERE m.conversation_id = fc.id
             AND CASE
                 WHEN p_is_admin THEN (m.is_admin_reply = FALSE AND m.read_by_admin = FALSE)
                 ELSE (m.is_admin_reply = TRUE AND m.read_by_user = FALSE)
             END),
            0
        ) as unread_count,
        fc.total as total_count
    FROM filtered_conversations fc;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- STORY-202 DB-M07: RPC for analytics summary with date range
-- Eliminates full-table-scan in backend/routes/analytics.py lines 78-83

CREATE OR REPLACE FUNCTION get_analytics_summary(
    p_user_id UUID,
    p_start_date TIMESTAMPTZ DEFAULT NULL,
    p_end_date TIMESTAMPTZ DEFAULT NULL
)
RETURNS TABLE (
    total_searches BIGINT,
    total_downloads BIGINT,
    total_opportunities BIGINT,
    total_value_discovered NUMERIC,
    member_since TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::BIGINT as total_searches,
        COUNT(*) FILTER (WHERE ss.total_filtered > 0)::BIGINT as total_downloads,
        COALESCE(SUM(ss.total_filtered), 0)::BIGINT as total_opportunities,
        COALESCE(SUM(ss.valor_total), 0)::NUMERIC as total_value_discovered,
        (SELECT p.created_at FROM profiles p WHERE p.id = p_user_id) as member_since
    FROM search_sessions ss
    WHERE ss.user_id = p_user_id
        AND (p_start_date IS NULL OR ss.created_at >= p_start_date)
        AND (p_end_date IS NULL OR ss.created_at <= p_end_date);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_conversations_with_unread_count IS
    'STORY-202 DB-M06: Eliminates N+1 query in conversation list';
COMMENT ON FUNCTION get_analytics_summary IS
    'STORY-202 DB-M07: Eliminates full-table-scan in analytics summary';
