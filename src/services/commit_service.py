import structlog
from typing import List
from datetime import datetime, timedelta
from sqlalchemy import select, func, desc
from fastapi import HTTPException

from ..models import (
    CommitResponse,
    CommitHistoryResponse,
    CommitMetrics,
    WebhookPayload,
    LocalCommitData,
    CommitSource,
    CommitStatus,
)
from ..database import get_db_service, CommitRecord

logger = structlog.get_logger(__name__)

class CommitService:
    """Core service for commit tracking operations."""

    def __init__(self):
        self.db_service = None

    def _validate_commit_data(self, commit_data: dict) -> bool:
        """Validate commit data to prevent test data from being stored."""
        # Check for test-related patterns
        test_patterns = [
            commit_data.get('commit_hash', '').startswith('test_'),
            commit_data.get('author_name', '').startswith('Test'),
            commit_data.get('repository_name', '').startswith('test_'),
            commit_data.get('commit_hash') == 'abc1234567890abcdef1234567890abcdef1234',
            'test' in commit_data.get('commit_message', '').lower(),
        ]
        
        if any(test_patterns):
            logger.warning(
                "Test data detected and rejected",
                commit_hash=commit_data.get('commit_hash'),
                author=commit_data.get('author_name'),
                repository=commit_data.get('repository_name'),
                message=commit_data.get('commit_message')
            )
            return False
        
        return True

    async def _get_db_service(self):
        """Get database service instance."""
        if self.db_service is None:
            self.db_service = await get_db_service()
        return self.db_service

    async def track_webhook_commit(
        self, webhook_payload: WebhookPayload
    ) -> List[CommitResponse]:
        """Track commits from GitHub webhook service."""
        logger.info(
                    "Processing webhook commits",
            event_type=webhook_payload.event_type,
            commit_count=len(webhook_payload.commits),
        )

        db_service = await self._get_db_service()
        responses = []

        async with db_service.get_session() as session:
            for commit_data in webhook_payload.commits:
                try:
                    # Validate commit data to prevent test data
                    if not self._validate_commit_data(commit_data):
                        logger.warning("Skipping test commit data", commit_hash=commit_data.get("id", ""))
                        continue
                    
                    # Create commit record
                    commit_record = CommitRecord(
                        commit_hash=commit_data.get("id", ""),
                        repository_name=webhook_payload.repository.get(
                                                                       "full_name", "unknown"
                        ),
                        author_name=commit_data.get("author", {}).get(
                                                                      "name", "Unknown"
                        ),
                        author_email=commit_data.get("author", {}).get("email", ""),
                        commit_message=commit_data.get("message", ""),
                        commit_date=datetime.fromisoformat(
                            commit_data.get("timestamp", "").replace("Z", "+00:00")
                        ),
                        source_type=CommitSource.WEBHOOK,
                        branch_name=webhook_payload.ref.replace("refs/heads/", ""),
                        files_changed=commit_data.get("modified", [])
                        + commit_data.get("added", [])
                        + commit_data.get("removed", []),
                        lines_added=commit_data.get("stats", {}).get("additions", 0),
                        lines_deleted=commit_data.get("stats", {}).get("deletions", 0),
                        parent_commits=commit_data.get("parents", []),
                        status=CommitStatus.PROCESSED,
                        processed_at=datetime.utcnow(),
                        metadata={
                            "webhook_event_type": webhook_payload.event_type,
                                "sender": webhook_payload.sender,
                                    "compare_url": webhook_payload.compare,
                        },
                    )

                    session.add(commit_record)
                    await session.commit()

                    # Create response
                    response = CommitResponse(
                        id=str(commit_record.id),
                        commit_hash=commit_record.commit_hash,
                        repository_name=commit_record.repository_name,
                        status=commit_record.status,
                        created_at=commit_record.created_at,
                        processed_at=commit_record.processed_at,
                    )
                    responses.append(response)

                    logger.info(
                                "Webhook commit tracked successfully",
                        commit_hash=commit_record.commit_hash[:8],
                        repository=commit_record.repository_name,
                    )

                except Exception as e:
                    logger.error(
                                 "Failed to track webhook commit",
                        commit_hash=commit_data.get("id", "")[:8],
                        error=str(e),
                    )
                    await session.rollback()

        return responses

    async def track_local_commit(self, local_commit: LocalCommitData) -> CommitResponse:
        """Track commits from local git repository."""
        logger.info(
                    "Processing local commit",
            commit_hash=local_commit.commit_hash[:8],
            repository_path=local_commit.repository_path,
        )

        db_service = await self._get_db_service()

        async with db_service.get_session() as session:
            try:
                # Validate commit data to prevent test data
                local_commit_dict = {
                    'commit_hash': local_commit.commit_hash,
                    'author_name': local_commit.author_name,
                    'repository_name': local_commit.repository_path.split("/")[-1],
                    'commit_message': local_commit.commit_message,
                }
                
                if not self._validate_commit_data(local_commit_dict):
                    logger.warning("Skipping test local commit data", commit_hash=local_commit.commit_hash[:8])
                    raise HTTPException(status_code=400, detail="Test data not allowed")
                
                # Create commit record
                commit_record = CommitRecord(
                    commit_hash=local_commit.commit_hash,
                    repository_name=local_commit.repository_path.split("/")[
                        -1
                    ],  # Extract repo name from path
                    author_name=local_commit.author_name,
                    author_email=local_commit.author_email,
                    commit_message=local_commit.commit_message,
                    commit_date=local_commit.commit_date,
                    source_type=CommitSource.LOCAL,
                    branch_name=local_commit.branch_name,
                    files_changed=local_commit.files_changed,
                    lines_added=local_commit.lines_added,
                    lines_deleted=local_commit.lines_deleted,
                    parent_commits=local_commit.parent_commits,
                    status=CommitStatus.PROCESSED,
                    processed_at=datetime.utcnow(),
                    metadata={
                        "repository_path": local_commit.repository_path,
                            "source": "local_git",
                    },
                )

                session.add(commit_record)
                await session.commit()

                # Create response
                response = CommitResponse(
                    id=str(commit_record.id),
                    commit_hash=commit_record.commit_hash,
                    repository_name=commit_record.repository_name,
                    status=commit_record.status,
                    created_at=commit_record.created_at,
                    processed_at=commit_record.processed_at,
                )

                logger.info(
                            "Local commit tracked successfully",
                    commit_hash=commit_record.commit_hash[:8],
                    repository=commit_record.repository_name,
                )

                return response

            except Exception as e:
                logger.error(
                             "Failed to track local commit",
                    commit_hash=local_commit.commit_hash[:8],
                    error=str(e),
                )
                await session.rollback()
                raise

    async def get_commit_history(
        self, repository_name: str, page: int = 1, page_size: int = 50
    ) -> CommitHistoryResponse:
        """Get commit history for a repository."""
        db_service = await self._get_db_service()

        async with db_service.get_session() as session:
            # Get total count
            count_query = select(func.count(CommitRecord.id)).where(
                CommitRecord.repository_name == repository_name
            )
            total_count = await session.scalar(count_query)

            # Get commits with pagination
            offset = (page - 1) * page_size
            commits_query = (
                select(CommitRecord)
                .where(CommitRecord.repository_name == repository_name)
                .order_by(desc(CommitRecord.commit_date))
                .offset(offset)
                .limit(page_size)
            )

            commit_records = await session.execute(commits_query)
            commits = commit_records.scalars().all()

            # Convert to response models
            commit_responses = [
                CommitResponse(
                    id=str(commit.id),
                    commit_hash=commit.commit_hash,
                    repository_name=commit.repository_name,
                    status=commit.status,
                    created_at=commit.created_at,
                    processed_at=commit.processed_at,
                )
                for commit in commits
            ]

            return CommitHistoryResponse(
                repository_name=repository_name,
                commits=commit_responses,
                total_count=total_count,
                page=page,
                page_size=page_size,
            )

    async def get_commit_metrics(self, repository_name: str) -> CommitMetrics:
        """Get commit metrics and statistics for a repository."""
        db_service = await self._get_db_service()

        async with db_service.get_session() as session:
            now = datetime.utcnow()
            today = now.date()
            week_ago = now - timedelta(days=7)
            month_ago = now - timedelta(days=30)

            # Total commits
            total_query = select(func.count(CommitRecord.id)).where(
                CommitRecord.repository_name == repository_name
            )
            total_commits = await session.scalar(total_query)

            # Commits today
            today_query = select(func.count(CommitRecord.id)).where(
                CommitRecord.repository_name == repository_name,
                func.date(CommitRecord.commit_date) == today,
            )
            commits_today = await session.scalar(today_query)

            # Commits this week
            week_query = select(func.count(CommitRecord.id)).where(
                CommitRecord.repository_name == repository_name,
                CommitRecord.commit_date >= week_ago,
            )
            commits_this_week = await session.scalar(week_query)

            # Commits this month
            month_query = select(func.count(CommitRecord.id)).where(
                CommitRecord.repository_name == repository_name,
                CommitRecord.commit_date >= month_ago,
            )
            commits_this_month = await session.scalar(month_query)

            # Most active author
            author_query = (
                select(
                    CommitRecord.author_name,
                    func.count(CommitRecord.id).label("commit_count"),
                )
                .where(CommitRecord.repository_name == repository_name)
                .group_by(CommitRecord.author_name)
                .order_by(desc("commit_count"))
                .limit(1)
            )

            author_result = await session.execute(author_query)
            author_row = author_result.first()
            most_active_author = author_row[0] if author_row else "Unknown"

            # Most active branch
            branch_query = (
                select(
                    CommitRecord.branch_name,
                    func.count(CommitRecord.id).label("commit_count"),
                )
                .where(
                    CommitRecord.repository_name == repository_name,
                    CommitRecord.branch_name.isnot(None),
                )
                .group_by(CommitRecord.branch_name)
                .order_by(desc("commit_count"))
                .limit(1)
            )

            branch_result = await session.execute(branch_query)
            branch_row = branch_result.first()
            most_active_branch = branch_row[0] if branch_row else "main"

            # Last commit date
            last_commit_query = (
                select(CommitRecord.commit_date)
                .where(CommitRecord.repository_name == repository_name)
                .order_by(desc(CommitRecord.commit_date))
                .limit(1)
            )

            last_commit_date = await session.scalar(last_commit_query)

            # Average commits per day (last 30 days)
            avg_commits_per_day = (
                commits_this_month / 30 if commits_this_month > 0 else 0.0
            )

            return CommitMetrics(
                repository_name=repository_name,
                total_commits=total_commits or 0,
                commits_today=commits_today or 0,
                commits_this_week=commits_this_week or 0,
                commits_this_month=commits_this_month or 0,
                average_commits_per_day=round(avg_commits_per_day, 2),
                most_active_author=most_active_author,
                most_active_branch=most_active_branch,
                last_commit_date=last_commit_date,
            )

# Global commit service instance
commit_service = CommitService()
