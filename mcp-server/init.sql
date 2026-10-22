CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS sprites (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    path        TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    folder      TEXT NOT NULL DEFAULT '',
    file_type   TEXT NOT NULL CHECK (file_type IN ('png', 'gif')),
    width       INTEGER NOT NULL,
    height      INTEGER NOT NULL,
    palette     TEXT,
    frame_count INTEGER NOT NULL DEFAULT 1,
    tags        TEXT[] NOT NULL DEFAULT '{}',
    created_by  TEXT NOT NULL DEFAULT 'agent' CHECK (created_by IN ('agent', 'manual')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS sprites_folder_idx    ON sprites (folder);
CREATE INDEX IF NOT EXISTS sprites_created_by_idx ON sprites (created_by);
CREATE INDEX IF NOT EXISTS sprites_tags_idx       ON sprites USING GIN (tags);
