CREATE TABLE IF NOT EXISTS chats (
    chat_id uuid PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    created_at TIMESTAMP(0) NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP(0) NOT NULL DEFAULT NOW(),
    msg_count INTEGER NOT NULL DEFAULT 0,
	chat_logs jsonb NULL,
	chat_state varchar(8) DEFAULT 'active'::character varying NULL,
	CONSTRAINT chats_chat_state_check CHECK ((((chat_state)::text = 'active'::text) OR ((chat_state)::text = 'deleted'::text)))
);