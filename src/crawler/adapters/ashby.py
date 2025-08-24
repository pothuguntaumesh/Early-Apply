import logging
from datetime import datetime,timezone
from typing import List
import aiohttp
from src.crawler.adapters.base import Adapter
from src.crawler.schemas import Job
from src.crawler.location_parsers.ashby import parse_ashby_location


logger = logging.getLogger("Ashby")
ISO_FMT = "%Y-%m-%dT%H:%M:%S.%f%z"

class AshbyAdapter(Adapter):
    async def fetch_jobs(self, company: str, url: str) -> List[Job]:    
        endpoint = url.rstrip("/")
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=20)
        ) as session:
            async with session.get(endpoint, headers={"Accept": "application/json"}) as resp:
                resp.raise_for_status()
                payload = await resp.json()

        jobs: List[Job] = []
        for j in payload.get("jobs", []):

            posted_at  = datetime.strptime(j["publishedAt"], ISO_FMT).astimezone(timezone.utc)
            updated_at = datetime.strptime(j["publishedAt"], ISO_FMT).astimezone(timezone.utc)

            # Parse location for Ashby using the new parser
            cities, countries, is_remote = parse_ashby_location(j)

            jobs.append(
                Job(
                    company       = company,
                    external_id   = str(j["id"]),
                    source_feed   = "Ashby",
                    department    = j["department"],
                    team          = j["team"],
                    employment_type = j["employmentType"],
                    title         = j["title"],

                    countries     = countries,
                    cities        = cities,
                    is_remote     = is_remote,

                    job_url       = j["jobUrl"],
                    apply_url     = j["applyUrl"],

                    posted_at     = posted_at,
                    job_updated_at= updated_at,
                )
            )

        logger.info("%s / %d jobs", company, len(jobs))
        return jobs
