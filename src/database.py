import structlog
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Integer,
    Text,
    JSON,
    Enum as SQLEnum,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from typing import Optional
import uuid

from .config import settings
from .models import CommitSource, CommitStatus

logger = structlog.get_logger(__name__)

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL, echo=settings.DEBUG, pool_pre_ping=True, pool_recycle=300
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Base class for models
Base = declarative_base()


class CommitRecord(Base):
    """Database model for commit records with diff support."""

    __tablename__ = "commits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    commit_hash = Column(String(40), nullable=False, index=True)
    repository_name = Column(String(255), nullable=False, index=True)
    author_name = Column(String(255), nullable=False)
    author_email = Column(String(255), nullable=False)
    commit_message = Column(Text, nullable=False)
    commit_date = Column(DateTime(timezone=True), nullable=False, index=True)
    source_type = Column(SQLEnum(CommitSource), nullable=False, index=True)
    branch_name = Column(String(255), nullable=True, index=True)
    files_changed = Column(JSON, nullable=True)
    lines_added = Column(Integer, nullable=True)
    lines_deleted = Column(Integer, nullable=True)
    parent_commits = Column(JSON, nullable=True)
    status = Column(SQLEnum(CommitStatus), nullable=False, default=CommitStatus.PENDING)
    commit_metadata = Column(JSON, nullable=True)
    
    # NEW: Diff content columns for production-ready analysis
    diff_content = Column(Text, nullable=True)  # Actual diff output
    file_diffs = Column(JSON, nullable=True)    # Structured diff data
    diff_hash = Column(String(64), nullable=True, index=True)  # For deduplication
    
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    processed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class CommitFileRecord(Base):
    """Database model for individual file changes in commits."""

    __tablename__ = "commit_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    commit_id = Column(UUID(as_uuid=True), ForeignKey("commits.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(500), nullable=False, index=True)
    file_path = Column(String(1000), nullable=True)
    file_extension = Column(String(20), nullable=True, index=True)
    status = Column(String(20), nullable=False, index=True)  # 'added', 'modified', 'deleted', 'renamed'
    additions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)
    diff_content = Column(Text, nullable=True)
    file_size_before = Column(Integer, nullable=True)
    file_size_after = Column(Integer, nullable=True)
    language = Column(String(50), nullable=True, index=True)
    complexity_score = Column(Integer, nullable=True)
    security_risk_level = Column(String(20), default="low", index=True)
    
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class DatabaseService:
    """Database service for commit tracking operations with diff support."""

    def __init__(self):
        self.session_factory = AsyncSessionLocal
        self._engine = engine

    async def get_session(self) -> AsyncSession:
        """Get database session."""
        return self.session_factory()

    async def create_tables(self):
        """Create database tables."""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")

    async def store_commit_with_diff(self, commit_data: dict) -> str:
        """Store commit with diff content and individual file records."""
        async with self.session_factory() as session:
            # Create commit record
            commit_record = CommitRecord(
                commit_hash=commit_data['commit_hash'],
                repository_name=commit_data['repository_name'],
                author_name=commit_data['author_name'],
                author_email=commit_data['author_email'],
                commit_message=commit_data['commit_message'],
                commit_date=commit_data['commit_date'],
                source_type=commit_data['source_type'],
                branch_name=commit_data.get('branch_name'),
                files_changed=commit_data.get('files_changed'),
                lines_added=commit_data.get('lines_added'),
                lines_deleted=commit_data.get('lines_deleted'),
                parent_commits=commit_data.get('parent_commits'),
                commit_metadata=commit_data.get('metadata'),
                diff_content=commit_data.get('diff_content', ''),
                file_diffs=commit_data.get('file_diffs', {}),
                diff_hash=commit_data.get('diff_hash', '')
            )
            session.add(commit_record)
            await session.commit()
            await session.refresh(commit_record)
            
            # Store individual file records
            file_diffs = commit_data.get('file_diffs', {})
            for filename, file_data in file_diffs.items():
                file_extension = filename.split('.')[-1] if '.' in filename else ''
                language = self._detect_language(file_extension)
                
                file_record = CommitFileRecord(
                    commit_id=commit_record.id,
                    filename=filename,
                    file_path=filename,
                    file_extension=file_extension,
                    status=file_data.get('status', 'modified'),
                    additions=len(file_data.get('additions', [])),
                    deletions=len(file_data.get('deletions', [])),
                    diff_content=file_data.get('diff_content', ''),
                    file_size_before=file_data.get('size_before'),
                    file_size_after=file_data.get('size_after'),
                    language=language,
                    complexity_score=file_data.get('complexity_score'),
                    security_risk_level=file_data.get('security_risk_level', 'low')
                )
                session.add(file_record)
            
            await session.commit()
            return str(commit_record.id)
    
    def _detect_language(self, file_extension: str) -> str:
        """Detect programming language from file extension."""
        language_map = {
            'py': 'Python',
            'js': 'JavaScript',
            'ts': 'TypeScript',
            'java': 'Java',
            'cpp': 'C++',
            'c': 'C',
            'cs': 'C#',
            'php': 'PHP',
            'rb': 'Ruby',
            'go': 'Go',
            'rs': 'Rust',
            'swift': 'Swift',
            'kt': 'Kotlin',
            'scala': 'Scala',
            'html': 'HTML',
            'css': 'CSS',
            'sql': 'SQL',
            'json': 'JSON',
            'xml': 'XML',
            'yaml': 'YAML',
            'yml': 'YAML',
            'md': 'Markdown',
            'txt': 'Text'
        }
        return language_map.get(file_extension.lower(), 'Unknown')

    async def get_commit_metadata(self, commit_id: str) -> Optional[dict]:
        """Get commit metadata (fast query, no diff content)."""
        async with self.session_factory() as session:
            result = await session.execute(
                "SELECT id, commit_hash, repository_name, author_name, author_email, "
                "commit_message, commit_date, source_type, branch_name, files_changed, "
                "lines_added, lines_deleted, parent_commits, status, commit_metadata, "
                "created_at, processed_at, updated_at "
                "FROM commits WHERE id = :commit_id",
                {"commit_id": commit_id}
            )
            row = result.fetchone()
            if row:
                return {
                    "id": str(row[0]),
                    "commit_hash": row[1],
                    "repository_name": row[2],
                    "author_name": row[3],
                    "author_email": row[4],
                    "commit_message": row[5],
                    "commit_date": row[6].isoformat() if row[6] else None,
                    "source_type": row[7],
                    "branch_name": row[8],
                    "files_changed": row[9],
                    "lines_added": row[10],
                    "lines_deleted": row[11],
                    "parent_commits": row[12],
                    "status": row[13],
                    "metadata": row[14],
                    "created_at": row[15].isoformat() if row[15] else None,
                    "processed_at": row[16].isoformat() if row[16] else None,
                    "updated_at": row[17].isoformat() if row[17] else None
                }
            return None

    async def get_commit_metadata_by_hash(self, commit_hash: str) -> Optional[dict]:
        """Get commit metadata by commit hash."""
        async with self.session_factory() as session:
            from sqlalchemy import text
            result = await session.execute(
                text("SELECT id, commit_hash, repository_name, author_name, author_email, "
                "commit_message, commit_date, source_type, branch_name, files_changed, "
                "lines_added, lines_deleted, parent_commits, status, commit_metadata, "
                "created_at, processed_at, updated_at "
                "FROM commits WHERE commit_hash = :commit_hash"),
                {"commit_hash": commit_hash}
            )
            row = result.fetchone()
            if row:
                return {
                    "id": str(row[0]),
                    "commit_hash": row[1],
                    "repository_name": row[2],
                    "author_name": row[3],
                    "author_email": row[4],
                    "commit_message": row[5],
                    "commit_date": row[6].isoformat() if row[6] else None,
                    "source_type": row[7],
                    "branch_name": row[8],
                    "files_changed": row[9],
                    "lines_added": row[10],
                    "lines_deleted": row[11],
                    "parent_commits": row[12],
                    "status": row[13],
                    "metadata": row[14],
                    "created_at": row[15].isoformat() if row[15] else None,
                    "processed_at": row[16].isoformat() if row[16] else None,
                    "updated_at": row[17].isoformat() if row[17] else None
                }
            return None

    async def get_commit_with_diff(self, commit_id: str) -> Optional[dict]:
        """Get commit with diff content (detailed view)."""
        async with self.session_factory() as session:
            result = await session.execute(
                "SELECT id, commit_hash, repository_name, author_name, author_email, "
                "commit_message, commit_date, source_type, branch_name, files_changed, "
                "lines_added, lines_deleted, parent_commits, status, commit_metadata, "
                "diff_content, file_diffs, created_at, processed_at, updated_at "
                "FROM commits WHERE id = :commit_id",
                {"commit_id": commit_id}
            )
            row = result.fetchone()
            if row:
                return {
                    "id": str(row[0]),
                    "commit_hash": row[1],
                    "repository_name": row[2],
                    "author_name": row[3],
                    "author_email": row[4],
                    "commit_message": row[5],
                    "commit_date": row[6].isoformat() if row[6] else None,
                    "source_type": row[7],
                    "branch_name": row[8],
                    "files_changed": row[9],
                    "lines_added": row[10],
                    "lines_deleted": row[11],
                    "parent_commits": row[12],
                    "status": row[13],
                    "metadata": row[14],
                    "diff_content": row[15],
                    "file_diffs": row[16],
                    "created_at": row[17].isoformat() if row[17] else None,
                    "processed_at": row[18].isoformat() if row[18] else None,
                    "updated_at": row[19].isoformat() if row[19] else None
                }
            return None

    async def get_commits_paginated(self, page: int = 1, limit: int = 20, 
                                  repository: Optional[str] = None, 
                                  author: Optional[str] = None,
                                  status: Optional[str] = None) -> dict:
        """Get commits with pagination and filtering."""
        async with self.session_factory() as session:
            offset = (page - 1) * limit
            
            # Build query with filters
            query = """
                SELECT id, commit_hash, repository_name, author_name, 
                       commit_message, commit_date, lines_added, lines_deleted, status 
                FROM commits 
                WHERE 1=1
            """
            params = {"limit": limit, "offset": offset}
            
            if repository:
                query += " AND repository_name = :repository"
                params["repository"] = repository
            
            if author:
                query += " AND author_name ILIKE :author"
                params["author"] = f"%{author}%"
            
            if status:
                query += " AND status = :status"
                params["status"] = status
            
            query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
            
            result = await session.execute(query, params)
            rows = result.fetchall()
            
            commits = [
                {
                    "id": str(row[0]),
                    "commit_hash": row[1],
                    "repository_name": row[2],
                    "author_name": row[3],
                    "commit_message": row[4],
                    "commit_date": row[5].isoformat() if row[5] else None,
                    "lines_added": row[6],
                    "lines_deleted": row[7],
                    "status": row[8]
                }
                for row in rows
            ]
            
            return {
                "commits": commits,
                "page": page,
                "limit": limit,
                "total": len(commits)
            }

    async def search_commits_fulltext(self, search_term: str, limit: int = 20) -> list:
        """Full-text search across commits."""
        async with self.session_factory() as session:
            result = await session.execute(
                "SELECT id, commit_hash, author_name, commit_message, "
                "lines_added, lines_deleted, created_at, "
                "ts_rank(search_vector, plainto_tsquery('english', :search_term)) as rank "
                "FROM commits "
                "WHERE search_vector @@ plainto_tsquery('english', :search_term) "
                "ORDER BY rank DESC, created_at DESC "
                "LIMIT :limit",
                {"search_term": search_term, "limit": limit}
            )
            rows = result.fetchall()
            return [
                {
                    "id": str(row[0]),
                    "commit_hash": row[1],
                    "author_name": row[2],
                    "commit_message": row[3],
                    "lines_added": row[4],
                    "lines_deleted": row[5],
                    "created_at": row[6].isoformat() if row[6] else None,
                    "rank": float(row[7]) if row[7] else 0.0
                }
                for row in rows
            ]

    async def get_commit_files(self, commit_id: str) -> list:
        """Get individual file changes for a commit."""
        async with self.session_factory() as session:
            result = await session.execute(
                "SELECT id, filename, file_path, file_extension, status, "
                "additions, deletions, diff_content, file_size_before, file_size_after, "
                "language, complexity_score, security_risk_level, created_at "
                "FROM commit_files WHERE commit_id = :commit_id ORDER BY filename",
                {"commit_id": commit_id}
            )
            rows = result.fetchall()
            return [
                {
                    "id": str(row[0]),
                    "filename": row[1],
                    "file_path": row[2],
                    "file_extension": row[3],
                    "status": row[4],
                    "additions": row[5],
                    "deletions": row[6],
                    "diff_content": row[7],
                    "file_size_before": row[8],
                    "file_size_after": row[9],
                    "language": row[10],
                    "complexity_score": row[11],
                    "security_risk_level": row[12],
                    "created_at": row[13].isoformat() if row[13] else None
                }
                for row in rows
            ]

    async def get_file_analysis(self, file_id: str) -> Optional[dict]:
        """Get detailed analysis for a specific file change."""
        async with self.session_factory() as session:
            result = await session.execute(
                "SELECT cf.*, c.commit_hash, c.commit_message, c.author_name "
                "FROM commit_files cf "
                "JOIN commits c ON cf.commit_id = c.id "
                "WHERE cf.id = :file_id",
                {"file_id": file_id}
            )
            row = result.fetchone()
            if row:
                return {
                    "id": str(row[0]),
                    "commit_id": str(row[1]),
                    "filename": row[2],
                    "file_path": row[3],
                    "file_extension": row[4],
                    "status": row[5],
                    "additions": row[6],
                    "deletions": row[7],
                    "diff_content": row[8],
                    "file_size_before": row[9],
                    "file_size_after": row[10],
                    "language": row[11],
                    "complexity_score": row[12],
                    "security_risk_level": row[13],
                    "commit_hash": row[16],
                    "commit_message": row[17],
                    "author_name": row[18],
                    "created_at": row[14].isoformat() if row[14] else None
                }
            return None

    async def get_commit_summary(self, commit_id: str) -> Optional[dict]:
        """Get commit summary with file statistics using the view."""
        async with self.session_factory() as session:
            result = await session.execute(
                "SELECT * FROM commit_summary WHERE id = :commit_id",
                {"commit_id": commit_id}
            )
            row = result.fetchone()
            if row:
                return {
                    "id": str(row[0]),
                    "commit_hash": row[1],
                    "repository_name": row[2],
                    "author_name": row[3],
                    "commit_message": row[4],
                    "commit_date": row[5].isoformat() if row[5] else None,
                    "source_type": row[6],
                    "branch_name": row[7],
                    "status": row[8],
                    "total_files_changed": row[9],
                    "total_additions": row[10],
                    "total_deletions": row[11],
                    "files_added": row[12],
                    "files_modified": row[13],
                    "files_deleted": row[14],
                    "critical_files": row[15],
                    "high_risk_files": row[16],
                    "created_at": row[17].isoformat() if row[17] else None,
                    "updated_at": row[18].isoformat() if row[18] else None
                }
            return None

    async def close(self):
        """Close database connections."""
        await self._engine.dispose()
        logger.info("Database connections closed")

    async def health_check(self) -> bool:
        """Check database health."""
        try:
            async with self.session_factory() as session:
                from sqlalchemy import text
                await session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return False


# Global database service instance
_db_service: Optional[DatabaseService] = None


async def get_db_service() -> DatabaseService:
    """Get database service instance."""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
        await _db_service.create_tables()
    return _db_service


async def close_db_service():
    """Close database service."""
    global _db_service
    if _db_service:
        await _db_service.close()
        _db_service = None
