# src/crawler/db_utils.py
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List

from sqlalchemy import select, update, func, tuple_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.dialects.postgresql import insert

from src.crawler.models import JobRecord
from src.notifications.models import JobAlertQueue
from src.crawler.schemas import Job

log = logging.getLogger(__name__)

# ───────────────────────────────────────────────
# single-row logic (NO commit inside)
# ───────────────────────────────────────────────
async def upsert_job(job: Job, session: AsyncSession) -> None:
    """
    Insert or update one job **using the caller-supplied session**.
    Caller must commit/rollback.
    """
    stmt = select(JobRecord).where(
        JobRecord.external_id == job.external_id,
        JobRecord.company == job.company,
        JobRecord.source_feed == job.source_feed,
    )
    result = await session.execute(stmt)
    existing: JobRecord | None = result.scalar_one_or_none()

    if existing:
        existing.title            = job.title
        existing.department       = job.department
        existing.team             = job.team
        existing.employment_type  = job.employment_type
        existing.countries        = job.countries
        existing.cities           = job.cities
        existing.is_remote        = job.is_remote
        existing.job_url          = job.job_url
        existing.apply_url        = job.apply_url
        existing.description      = job.description
        existing.posted_at        = job.posted_at
        existing.job_updated_at   = job.job_updated_at
        # keep updated_at column auto-updating via onupdate=func.now()
    else:
        session.add(
            JobRecord(
                external_id     = job.external_id,
                company         = job.company,
                source_feed     = job.source_feed,
                title           = job.title,
                department      = job.department,
                team            = job.team,
                employment_type = job.employment_type,
                countries       = job.countries,
                cities          = job.cities,
                is_remote       = job.is_remote,
                job_url         = job.job_url,
                apply_url       = job.apply_url,
                description     = job.description,
                posted_at       = job.posted_at,
                job_updated_at  = job.job_updated_at,
                is_active       = True,
            )
        )

async def deactivate_missing(
    company: str,
    source_feed: str,
    seen_ids: List[str],
    session: AsyncSession,
) -> None:
    """Mark rows not seen in this crawl as inactive."""
    await session.execute(
        update(JobRecord)
        .where(
            JobRecord.company == company,
            JobRecord.source_feed == source_feed,
            JobRecord.external_id.not_in(seen_ids),
        )
        .values(is_active=False)
    )

async def bulk_upsert_jobs(jobs: List[Job], session: AsyncSession) -> None:
    """
    Bulk upsert jobs with error handling.
    """
    if not jobs:
        return
    
    try:
        # Convert Job objects to dictionaries for bulk insert
        job_data = []
        for job in jobs:
            job_data.append({
                "external_id": job.external_id,
                "company": job.company, 
                "source_feed": job.source_feed,
                "title": job.title,
                "department": job.department,
                "team": job.team,
                "employment_type": job.employment_type,
                "countries": job.countries,
                "cities": job.cities,
                "is_remote": job.is_remote,
                "job_url": job.job_url,
                "apply_url": job.apply_url,
                "description": job.description,
                "posted_at": job.posted_at,
                "job_updated_at": job.job_updated_at,
                "is_active": True,
            })
        
        # Use PostgreSQL's INSERT ... ON CONFLICT DO UPDATE
        stmt = insert(JobRecord).values(job_data)
        
        update_dict = {
            "title": stmt.excluded.title,
            "department": stmt.excluded.department,
            "team": stmt.excluded.team,
            "employment_type": stmt.excluded.employment_type,
            "countries": stmt.excluded.countries,
            "cities": stmt.excluded.cities,
            "is_remote": stmt.excluded.is_remote,
            "job_url": stmt.excluded.job_url,
            "apply_url": stmt.excluded.apply_url,
            "description": stmt.excluded.description,
            "posted_at": stmt.excluded.posted_at,
            "job_updated_at": stmt.excluded.job_updated_at,
            "is_active": stmt.excluded.is_active,
            "updated_at": func.now(),
        }
        
        upsert_stmt = stmt.on_conflict_do_update(
            constraint="uq_job_key",
            set_=update_dict
        )
        
        await session.execute(upsert_stmt)
        
    except SQLAlchemyError as exc:
        log.error("Database error during bulk upsert: %s", exc)
        await session.rollback()
        raise  # Re-raise to be handled by caller
    except Exception as exc:
        log.error("Unexpected error during bulk upsert: %s", exc)
        await session.rollback()
        raise

async def enqueue_job_alerts(jobs: List[Job], session: AsyncSession) -> None:
    if not jobs:
        return
    
    
    job_alerts=await session.execute(
    select(JobRecord).where(
        tuple_(
            JobRecord.external_id,
            JobRecord.company,
            JobRecord.source_feed
        ).in_([
            (job.external_id, job.company, job.source_feed)
            for job in jobs
        ])
    )
)
    job_alerts=job_alerts.scalars().all()

    for j in job_alerts:
        session.add(JobAlertQueue(job_id=j.id))