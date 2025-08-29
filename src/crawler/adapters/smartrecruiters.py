import logging
import asyncio
from typing import List
import aiohttp
from src.crawler.adapters.base import Adapter
from src.crawler.schemas import Job
from datetime import datetime, timezone

logger = logging.getLogger("SmartRecruiters")

class SmartRecruitersAdapter(Adapter):

    async def fetch_jobs(self, company: str, url: str) -> List[Job]:
        endpoint = url.rstrip("/")
        offset = 0
        limit = 100
        jobs: List[Job] = []
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=20)
        ) as session:
            while True:
                paginated_url = f"{endpoint}?offset={offset}&limit={limit}"
                async with session.get(paginated_url, headers={"Accept": "application/json"}) as resp:
                    resp.raise_for_status()
                    data= await resp.json()


                    for j in data.get("content", []):
                        try:
                            date_str = j["releasedDate"]
                            if date_str.endswith('Z'):
                                date_str = date_str[:-1] + '+00:00'
                            posted_at = datetime.fromisoformat(date_str).astimezone(timezone.utc)

                            # Handle location data safely
                            location = j.get("location", {})
                            country = location.get("country") if location else None
                            city = location.get("city") if location else None
                            is_remote = location.get("remote", False) if location else False

                            jobs.append(
                            Job(
                                company       = company,
                                external_id   = str(j["id"]),
                                source_feed   = "SmartRecruiters",

                                title         = j["name"],

                                countries     = [country] if country else [],
                                cities        = [city] if city else [],
                                is_remote     = is_remote,

                                job_url       = "No URL, check the job page",
                                apply_url     = "No URL, check the job page",

                                posted_at     = posted_at,
                                job_updated_at= posted_at,
                            )
                            )
                        except Exception as e:
                            logger.error(f"Error processing job {j.get('id', 'unknown')}: {e}")
                            continue

                if len(data.get("content", [])) < limit:
                    break

                offset += limit

        logger.info("%s – %d jobs", company, len(jobs))
        print(f"Fetched {len(jobs)} jobs for {company}")
        return jobs










# if __name__ == "__main__":
#     adapter = SmartRecruitersAdapter()
#     asyncio.run(adapter.fetch_jobs("ServiceNow", "https://api.smartrecruiters.com/v1/companies/servicenow/postings"))