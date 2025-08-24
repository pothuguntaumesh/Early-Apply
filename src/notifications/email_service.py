import logging
from collections import defaultdict
from datetime import datetime
import asyncio

from sqlalchemy import select, delete

from src.crawler.db import get_session
from src.crawler.models import JobRecord
from src.notifications.models import UserJobPref, JobAlert, JobAlertQueue
from src.notifications.filters import match_job
from src.notifications.notifier import send_email

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def process_alerts():
    async for session in get_session():
        alerts_result = await session.execute(select(JobAlertQueue))
        alerts = alerts_result.scalars().all()
        if not alerts:
            log.info("No job alerts to process")
            return

        job_ids = [a.job_id for a in alerts]
        jobs_result = await session.execute(select(JobRecord).where(JobRecord.id.in_(job_ids)))
        jobs = jobs_result.scalars().all()

        prefs_result = await session.execute(select(UserJobPref))
        user_prefs = prefs_result.scalars().all()

        all_roles = {r.lower() for p in user_prefs for r in p.roles}
        roles_to_jobs = defaultdict(list)
        for job in jobs:
            title = job.title.lower()
            for role in all_roles:
                if role in title:
                    roles_to_jobs[role].append(job)

        for pref in user_prefs:
            matched = []
            for role in pref.roles:
                for job in roles_to_jobs.get(role.lower(), []):
                    if match_job(job, pref):
                        matched.append(job)
            if matched:
                await send_email(pref.email, matched)
                for job in matched:
                    session.add(
                        JobAlert(
                            user_id=pref.user_id,
                            job_id=job.id,
                            sent_at=datetime.now(),
                        )
                    )

        await session.execute(delete(JobAlertQueue).where(JobAlertQueue.id.in_([a.id for a in alerts])))
        await session.commit()


if __name__ == "__main__":
    asyncio.run(process_alerts())
