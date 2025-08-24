from datetime import datetime, timezone
from typing import List
import aiohttp, logging

from src.crawler.adapters.base import Adapter
from src.crawler.schemas import Job
from src.crawler.location_parsers.greenhouse import parse_greenhouse_location

logger = logging.getLogger("Greenhouse")
ISO_FMT = "%Y-%m-%dT%H:%M:%S%z"

class GreenhouseAdapter(Adapter):

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

            posted_at  = datetime.strptime(j["first_published"], ISO_FMT).astimezone(timezone.utc)
            updated_at = datetime.strptime(j["updated_at"],      ISO_FMT).astimezone(timezone.utc)

            cities, countries, is_remote = parse_greenhouse_location(j["location"]["name"])

            jobs.append(
                Job(
                    company       = company,
                    external_id   = str(j["id"]),
                    source_feed   = "Greenhouse",

                    title         = j["title"],

                    countries     = countries,
                    cities        = cities,
                    is_remote     = is_remote,

                    job_url       = j["absolute_url"],
                    apply_url     = j["absolute_url"],

                    posted_at     = posted_at,
                    job_updated_at= updated_at,
                )
            )

        logger.info("%s – %d jobs", company, len(jobs))
        return jobs
