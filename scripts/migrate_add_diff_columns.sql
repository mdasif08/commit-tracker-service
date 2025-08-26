-- Migration script to add diff columns to existing commits table
-- Run this script on your existing PostgreSQL database

-- Add diff content columns to existing commits table
ALTER TABLE commits ADD COLUMN IF NOT EXISTS diff_content TEXT;
ALTER TABLE commits ADD COLUMN IF NOT EXISTS file_diffs JSONB;
ALTER TABLE commits ADD COLUMN IF NOT EXISTS diff_hash VARCHAR(64);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_commits_diff_hash ON commits(diff_hash);
CREATE INDEX IF NOT EXISTS idx_commits_diff_content ON commits USING gin(to_tsvector('english', diff_content));

-- Add search vector column for full-text search
ALTER TABLE commits ADD COLUMN IF NOT EXISTS search_vector tsvector GENERATED ALWAYS AS (
    to_tsvector('english', 
        coalesce(commit_message, '') || ' ' || 
        coalesce(author_name, '') || ' ' || 
        coalesce(diff_content, '')
    )
) STORED;

-- Create full-text search index
CREATE INDEX IF NOT EXISTS idx_commits_search ON commits USING GIN(search_vector);

-- Update existing commits to have empty diff content (if needed)
UPDATE commits SET diff_content = '', file_diffs = '{}', diff_hash = '' WHERE diff_content IS NULL;

-- Grant permissions (if needed)
GRANT ALL PRIVILEGES ON TABLE commits TO commit_user;

-- Verify the migration
SELECT 
    column_name, 
    data_type, 
    is_nullable 
FROM information_schema.columns 
WHERE table_name = 'commits' 
AND column_name IN ('diff_content', 'file_diffs', 'diff_hash', 'search_vector')
ORDER BY column_name;

-- Show indexes
SELECT 
    indexname, 
    indexdef 
FROM pg_indexes 
WHERE tablename = 'commits' 
AND indexname LIKE '%diff%' OR indexname LIKE '%search%'
ORDER BY indexname;
