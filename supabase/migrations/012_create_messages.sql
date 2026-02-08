-- Migration 012: Create InMail messaging system (conversations + messages)
-- Enables internal support messaging between users and admins.

-- ============================================================================
-- Table: conversations
-- ============================================================================
CREATE TABLE IF NOT EXISTS conversations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    subject text NOT NULL CHECK (char_length(subject) <= 200),
    category text NOT NULL CHECK (category IN ('suporte', 'sugestao', 'funcionalidade', 'bug', 'outro')),
    status text NOT NULL DEFAULT 'aberto' CHECK (status IN ('aberto', 'respondido', 'resolvido')),
    last_message_at timestamptz NOT NULL DEFAULT now(),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- ============================================================================
-- Table: messages
-- ============================================================================
CREATE TABLE IF NOT EXISTS messages (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    body text NOT NULL CHECK (char_length(body) >= 1 AND char_length(body) <= 5000),
    is_admin_reply boolean NOT NULL DEFAULT false,
    read_by_user boolean NOT NULL DEFAULT false,
    read_by_admin boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now()
);

-- ============================================================================
-- Indexes
-- ============================================================================
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_last_message ON conversations(last_message_at DESC);
CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at);

-- Partial indexes for unread counts (efficient badge queries)
CREATE INDEX idx_messages_unread_by_user
    ON messages(conversation_id)
    WHERE is_admin_reply = true AND read_by_user = false;

CREATE INDEX idx_messages_unread_by_admin
    ON messages(conversation_id)
    WHERE is_admin_reply = false AND read_by_admin = false;

-- ============================================================================
-- Trigger: update last_message_at on new message
-- ============================================================================
CREATE OR REPLACE FUNCTION update_conversation_last_message()
RETURNS trigger AS $$
BEGIN
    UPDATE conversations
    SET last_message_at = NEW.created_at,
        updated_at = now()
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_conversation_last_message
    AFTER INSERT ON messages
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_last_message();

-- ============================================================================
-- RLS Policies
-- ============================================================================
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Conversations: users see own, admins see all
CREATE POLICY conversations_select_own ON conversations
    FOR SELECT USING (
        auth.uid() = user_id
        OR EXISTS (SELECT 1 FROM profiles WHERE profiles.id = auth.uid() AND profiles.is_admin = true)
    );

CREATE POLICY conversations_insert_own ON conversations
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY conversations_update_admin ON conversations
    FOR UPDATE USING (
        EXISTS (SELECT 1 FROM profiles WHERE profiles.id = auth.uid() AND profiles.is_admin = true)
    );

-- Messages: users see messages in own conversations, admins see all
CREATE POLICY messages_select ON messages
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM conversations c
            WHERE c.id = messages.conversation_id
            AND (c.user_id = auth.uid()
                 OR EXISTS (SELECT 1 FROM profiles WHERE profiles.id = auth.uid() AND profiles.is_admin = true))
        )
    );

CREATE POLICY messages_insert_user ON messages
    FOR INSERT WITH CHECK (
        auth.uid() = sender_id
        AND EXISTS (
            SELECT 1 FROM conversations c
            WHERE c.id = messages.conversation_id
            AND (c.user_id = auth.uid()
                 OR EXISTS (SELECT 1 FROM profiles WHERE profiles.id = auth.uid() AND profiles.is_admin = true))
        )
    );

-- Messages: allow updating read status
CREATE POLICY messages_update_read ON messages
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM conversations c
            WHERE c.id = messages.conversation_id
            AND (c.user_id = auth.uid()
                 OR EXISTS (SELECT 1 FROM profiles WHERE profiles.id = auth.uid() AND profiles.is_admin = true))
        )
    );
