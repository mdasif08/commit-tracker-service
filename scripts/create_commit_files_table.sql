-- Create commit_files table for detailed file-level analysis
-- This table will store individual file changes for each commit

CREATE TABLE IF NOT EXISTS commit_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    commit_id UUID NOT NULL REFERENCES commits(id) ON DELETE CASCADE,
    filename VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000),
    file_extension VARCHAR(20),
    status VARCHAR(20) NOT NULL CHECK (status IN ('added', 'modified', 'deleted', 'renamed')),
    additions INTEGER DEFAULT 0,
    deletions INTEGER DEFAULT 0,
    diff_content TEXT,
    file_size_before BIGINT,
    file_size_after BIGINT,
    language VARCHAR(50), -- Programming language detection
    complexity_score INTEGER, -- Code complexity metrics
    security_risk_level VARCHAR(20) DEFAULT 'low' CHECK (security_risk_level IN ('low', 'medium', 'high', 'critical')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_commit_files_commit_id ON commit_files(commit_id);
CREATE INDEX IF NOT EXISTS idx_commit_files_filename ON commit_files(filename);
CREATE INDEX IF NOT EXISTS idx_commit_files_status ON commit_files(status);
CREATE INDEX IF NOT EXISTS idx_commit_files_extension ON commit_files(file_extension);
CREATE INDEX IF NOT EXISTS idx_commit_files_language ON commit_files(language);
CREATE INDEX IF NOT EXISTS idx_commit_files_security_risk ON commit_files(security_risk_level);

-- Create composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_commit_files_commit_status ON commit_files(commit_id, status);
CREATE INDEX IF NOT EXISTS idx_commit_files_extension_risk ON commit_files(file_extension, security_risk_level);

-- Create full-text search index for diff content
CREATE INDEX IF NOT EXISTS idx_commit_files_diff_search ON commit_files USING gin(to_tsvector('english', diff_content));

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_commit_files_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_commit_files_updated_at 
    BEFORE UPDATE ON commit_files 
    FOR EACH ROW 
    EXECUTE FUNCTION update_commit_files_updated_at();

-- Grant permissions
GRANT ALL PRIVILEGES ON TABLE commit_files TO commit_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO commit_user;

-- Create view for commit summary with file statistics
CREATE OR REPLACE VIEW commit_summary AS
SELECT 
    c.id,
    c.commit_hash,
    c.repository_name,
    c.author_name,
    c.commit_message,
    c.commit_date,
    c.source_type,
    c.branch_name,
    c.status,
    COUNT(cf.id) as total_files_changed,
    SUM(cf.additions) as total_additions,
    SUM(cf.deletions) as total_deletions,
    COUNT(CASE WHEN cf.status = 'added' THEN 1 END) as files_added,
    COUNT(CASE WHEN cf.status = 'modified' THEN 1 END) as files_modified,
    COUNT(CASE WHEN cf.status = 'deleted' THEN 1 END) as files_deleted,
    COUNT(CASE WHEN cf.security_risk_level = 'critical' THEN 1 END) as critical_files,
    COUNT(CASE WHEN cf.security_risk_level = 'high' THEN 1 END) as high_risk_files,
    c.created_at,
    c.updated_at
FROM commits c
LEFT JOIN commit_files cf ON c.id = cf.commit_id
GROUP BY c.id, c.commit_hash, c.repository_name, c.author_name, c.commit_message, 
         c.commit_date, c.source_type, c.branch_name, c.status, c.created_at, c.updated_at;

-- Grant permissions on view
GRANT SELECT ON commit_summary TO commit_user;
