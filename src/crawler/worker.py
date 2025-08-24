import asyncio, logging, importlib.resources, yaml, sqlalchemy, sqlalchemy.orm, sqlalchemy.ext.asyncio
from typing import List

from src.crawler.adapters import ADAPTER_REGISTRY
from src.crawler.db_utils import bulk_upsert_jobs, deactivate_missing, enqueue_job_alerts
from src.crawler.schemas import Job 
from src.crawler.db import init_db, get_session
from src.crawler.models import JobRecord
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

log = logging.getLogger("worker")
logging.basicConfig(level=logging.INFO)

# ── helpers ────────────────────────────────────────────────────────────
def load_companies() -> List[dict]:
    yaml_path = importlib.resources.files("src.crawler") / "companies.yaml"
    with open(yaml_path) as f:
        return yaml.safe_load(f)


# ── adapter wrapper with full error handling ──────────────────────────
async def process_feed(company: str, feed: dict, sem: asyncio.Semaphore):
    """Process a single company feed with comprehensive error handling."""
    try:
        adapter_cls = ADAPTER_REGISTRY.get(feed["ats"])
        if not adapter_cls:
            log.warning("No adapter for %s", feed["ats"])
            return

        # ── API fetch (with existing error handling) ──────────────────
        async with sem:                       
            try:
                adapter = adapter_cls()
                jobs: List[Job] = await adapter.fetch_jobs(company, feed["url"])
            except Exception as exc:
                log.error("Fetch error %s / %s: %s", company, feed["ats"], exc)
                return

        # ── Database operations with error handling ───────────────────
        try:
            async for session in get_session():
                existing_jobs= await session.execute(
                    select(JobRecord)
                    .where(JobRecord.company==company, JobRecord.source_feed==feed["ats"]))
                
                existing_jobs=existing_jobs.scalars().all()
                existing_jobs_map={job.external_id:job for job in existing_jobs}

                upsert_jobs=[]
                jobs_to_alert=[]
                for job in jobs:
                    existing_job= existing_jobs_map.get(job.external_id)
                    if not existing_job:
                        upsert_jobs.append(job)
                        jobs_to_alert.append(job)
                    else:
                        if existing_job.job_updated_at !=job.job_updated_at or existing_job.posted_at !=job.posted_at:
                            upsert_jobs.append(job)
                            jobs_to_alert.append(job)
            
                if upsert_jobs:
                    await bulk_upsert_jobs(upsert_jobs, session)

                if jobs_to_alert:
                    await enqueue_job_alerts(jobs_to_alert, session)
                
                seen_ids = [job.external_id for job in jobs]
                await deactivate_missing(company, feed["ats"], seen_ids, session)
                await session.commit()

                log.info("%s / %s – upserted %d rows", company, feed["ats"], len(seen_ids))
                
        except Exception as exc:
            log.error("Database error %s / %s: %s", company, feed["ats"], exc)
            # Don't re-raise - let other feeds continue
            return
            
    except Exception as exc:
        # Catch-all for any unexpected errors
        log.error("Unexpected error processing %s / %s: %s", company, feed["ats"], exc)
        # Don't re-raise - let other feeds continue

# ── main orchestrator with return_exceptions=True ─────────────────────
async def run_once(concurrency: int = 10):
    sem = asyncio.Semaphore(concurrency)
    companies = load_companies()
    tasks = [
        process_feed(company["name"], feed, sem)
        for company in companies
        for feed in company.get("feeds", [])
    ]
    
    # ⚠️ CRITICAL: Use return_exceptions=True to prevent cascade failures
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Optional: Log any unexpected exceptions that slipped through
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            log.error("Task %d failed with unexpected exception: %s", i, result)

async def main():
    await init_db()
    await run_once()

# ── CLI entry ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    asyncio.run(main())
