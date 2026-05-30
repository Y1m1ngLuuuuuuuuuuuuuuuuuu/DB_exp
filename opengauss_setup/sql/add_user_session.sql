CREATE TABLE IF NOT EXISTS user_session (
    session_id   BIGSERIAL   NOT NULL,
    user_id      BIGINT      NOT NULL,
    token_hash   VARCHAR(64) NOT NULL,
    created_at   TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at   TIMESTAMP   NOT NULL,
    revoked_at   TIMESTAMP,
    last_seen_at TIMESTAMP,
    PRIMARY KEY (session_id),
    CONSTRAINT uq_user_session_token UNIQUE (token_hash),
    CONSTRAINT fk_user_session_user FOREIGN KEY (user_id) REFERENCES user_account (user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_user_session_user ON user_session (user_id);
CREATE INDEX IF NOT EXISTS idx_user_session_valid ON user_session (token_hash, expires_at, revoked_at);
