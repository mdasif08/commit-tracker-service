"""Initial database schema

Revision ID: 001
Revises: 
Create Date: 2025-08-29 17:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create commits table
    op.create_table('commits',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('commit_hash', sa.String(length=40), nullable=False),
        sa.Column('repository_name', sa.String(length=255), nullable=False),
        sa.Column('author_name', sa.String(length=255), nullable=False),
        sa.Column('author_email', sa.String(length=255), nullable=False),
        sa.Column('commit_message', sa.Text(), nullable=False),
        sa.Column('commit_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('source_type', sa.Enum('WEBHOOK', 'LOCAL', 'GIT_SYNC', name='commitsource'), nullable=False),
        sa.Column('branch_name', sa.String(length=255), nullable=True),
        sa.Column('files_changed', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('lines_added', sa.Integer(), nullable=True),
        sa.Column('lines_deleted', sa.Integer(), nullable=True),
        sa.Column('parent_commits', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSED', 'FAILED', name='commitstatus'), nullable=False),
        sa.Column('commit_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('diff_content', sa.Text(), nullable=True),
        sa.Column('file_diffs', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('diff_hash', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better performance
    op.create_index(op.f('ix_commits_commit_hash'), 'commits', ['commit_hash'], unique=False)
    op.create_index(op.f('ix_commits_repository_name'), 'commits', ['repository_name'], unique=False)
    op.create_index(op.f('ix_commits_author_name'), 'commits', ['author_name'], unique=False)
    op.create_index(op.f('ix_commits_commit_date'), 'commits', ['commit_date'], unique=False)
    op.create_index(op.f('ix_commits_source_type'), 'commits', ['source_type'], unique=False)
    op.create_index(op.f('ix_commits_branch_name'), 'commits', ['branch_name'], unique=False)
    op.create_index(op.f('ix_commits_status'), 'commits', ['status'], unique=False)
    op.create_index(op.f('ix_commits_diff_hash'), 'commits', ['diff_hash'], unique=False)
    op.create_index(op.f('ix_commits_created_at'), 'commits', ['created_at'], unique=False)
    
    # Create commit_files table
    op.create_table('commit_files',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('commit_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(length=500), nullable=False),
        sa.Column('file_path', sa.String(length=1000), nullable=True),
        sa.Column('file_extension', sa.String(length=20), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('additions', sa.Integer(), nullable=True),
        sa.Column('deletions', sa.Integer(), nullable=True),
        sa.Column('diff_content', sa.Text(), nullable=True),
        sa.Column('file_size_before', sa.Integer(), nullable=True),
        sa.Column('file_size_after', sa.Integer(), nullable=True),
        sa.Column('language', sa.String(length=50), nullable=True),
        sa.Column('complexity_score', sa.Integer(), nullable=True),
        sa.Column('security_risk_level', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['commit_id'], ['commits.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for commit_files
    op.create_index(op.f('ix_commit_files_commit_id'), 'commit_files', ['commit_id'], unique=False)
    op.create_index(op.f('ix_commit_files_filename'), 'commit_files', ['filename'], unique=False)
    op.create_index(op.f('ix_commit_files_file_extension'), 'commit_files', ['file_extension'], unique=False)
    op.create_index(op.f('ix_commit_files_status'), 'commit_files', ['status'], unique=False)
    op.create_index(op.f('ix_commit_files_language'), 'commit_files', ['language'], unique=False)
    op.create_index(op.f('ix_commit_files_security_risk_level'), 'commit_files', ['security_risk_level'], unique=False)
    
    # Create full-text search index for commits
    op.execute("""
        ALTER TABLE commits 
        ADD COLUMN search_vector tsvector 
        GENERATED ALWAYS AS (
            setweight(to_tsvector('english', coalesce(commit_message, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(author_name, '')), 'B') ||
            setweight(to_tsvector('english', coalesce(repository_name, '')), 'C')
        ) STORED
    """)
    
    op.create_index('ix_commits_search_vector', 'commits', ['search_vector'], postgresql_using='gin')
    
    # Create materialized view for commit statistics
    op.execute("""
        CREATE MATERIALIZED VIEW commit_statistics AS
        SELECT 
            DATE_TRUNC('day', commit_date) as date,
            COUNT(*) as total_commits,
            COUNT(DISTINCT author_name) as unique_authors,
            SUM(lines_added) as total_lines_added,
            SUM(lines_deleted) as total_lines_deleted,
            AVG(lines_added + lines_deleted) as avg_commit_size
        FROM commits
        GROUP BY DATE_TRUNC('day', commit_date)
        ORDER BY date DESC
    """)
    
    # Create index on materialized view
    op.create_index('ix_commit_statistics_date', 'commit_statistics', ['date'], unique=True)


def downgrade() -> None:
    # Drop materialized view
    op.execute("DROP MATERIALIZED VIEW IF EXISTS commit_statistics")
    
    # Drop indexes
    op.drop_index('ix_commits_search_vector', table_name='commits')
    op.drop_index(op.f('ix_commits_created_at'), table_name='commits')
    op.drop_index(op.f('ix_commits_diff_hash'), table_name='commits')
    op.drop_index(op.f('ix_commits_status'), table_name='commits')
    op.drop_index(op.f('ix_commits_branch_name'), table_name='commits')
    op.drop_index(op.f('ix_commits_source_type'), table_name='commits')
    op.drop_index(op.f('ix_commits_commit_date'), table_name='commits')
    op.drop_index(op.f('ix_commits_author_name'), table_name='commits')
    op.drop_index(op.f('ix_commits_repository_name'), table_name='commits')
    op.drop_index(op.f('ix_commits_commit_hash'), table_name='commits')
    
    op.drop_index(op.f('ix_commit_files_security_risk_level'), table_name='commit_files')
    op.drop_index(op.f('ix_commit_files_language'), table_name='commit_files')
    op.drop_index(op.f('ix_commit_files_status'), table_name='commit_files')
    op.drop_index(op.f('ix_commit_files_file_extension'), table_name='commit_files')
    op.drop_index(op.f('ix_commit_files_filename'), table_name='commit_files')
    op.drop_index(op.f('ix_commit_files_commit_id'), table_name='commit_files')
    
    # Drop tables
    op.drop_table('commit_files')
    op.drop_table('commits')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS commitstatus")
    op.execute("DROP TYPE IF EXISTS commitsource")


