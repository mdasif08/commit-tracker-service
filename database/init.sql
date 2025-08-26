-- Initialize Commit Tracker Service Database
-- This script creates the necessary tables and indexes

-- Create commits table
CREATE TABLE IF NOT EXISTS commits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    commit_hash VARCHAR(40) NOT NULL,
    repository_name VARCHAR(255) NOT NULL,
    author_name VARCHAR(255) NOT NULL,
    author_email VARCHAR(255) NOT NULL,
    commit_message TEXT NOT NULL,
    commit_date TIMESTAMP NOT NULL,
    source_type VARCHAR(20) NOT NULL CHECK (source_type IN ('webhook', 'local')),
    branch_name VARCHAR(255),
    files_changed JSONB,
    lines_added INTEGER,
    lines_deleted INTEGER,
    parent_commits JSONB,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processed', 'failed')),
    metadata JSONB,
    
    -- NEW: Diff content columns for production-ready analysis
    diff_content TEXT,
    file_diffs JSONB,
    diff_hash VARCHAR(64),  -- For deduplication
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Search optimization for full-text search
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english', 
            coalesce(commit_message, '') || ' ' || 
            coalesce(author_name, '') || ' ' || 
            coalesce(diff_content, '')
        )
    ) STORED
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_commits_repository_name ON commits(repository_name);
CREATE INDEX IF NOT EXISTS idx_commits_commit_hash ON commits(commit_hash);
CREATE INDEX IF NOT EXISTS idx_commits_commit_date ON commits(commit_date);
CREATE INDEX IF NOT EXISTS idx_commits_source_type ON commits(source_type);
CREATE INDEX IF NOT EXISTS idx_commits_status ON commits(status);
CREATE INDEX IF NOT EXISTS idx_commits_author_name ON commits(author_name);
CREATE INDEX IF NOT EXISTS idx_commits_branch_name ON commits(branch_name);

-- NEW: Production indexes for diff content and search
CREATE INDEX IF NOT EXISTS idx_commits_diff_hash ON commits(diff_hash);
CREATE INDEX IF NOT EXISTS idx_commits_search ON commits USING GIN(search_vector);
CREATE INDEX IF NOT EXISTS idx_commits_diff_content ON commits USING gin(to_tsvector('english', diff_content));

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_commits_updated_at 
    BEFORE UPDATE ON commits 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions
GRANT ALL PRIVILEGES ON TABLE commits TO commit_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO commit_user;
