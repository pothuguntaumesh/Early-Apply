import logging
from typing import List
import aiohttp
from datetime import datetime, timezone
from src.crawler.adapters.base import Adapter
from src.crawler.schemas import Job
from src.crawler.location_parsers.lever import parse_lever_location


logger = logging.getLogger("Lever")

class LeverAdapter(Adapter):
    
    async def fetch_jobs(self, company: str, url: str) -> List[Job]:
        endpoint = url.rstrip("/")
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=20)
        ) as session:
            async with session.get(endpoint, headers={"Accept": "application/json"}) as resp:
                resp.raise_for_status()
                payload = await resp.json()

        jobs: List[Job] = []

        for j in payload:
            posted_at = datetime.fromtimestamp(j["createdAt"]/1000, tz=timezone.utc)
            
            # Parse location using the Lever location parser
            cities, countries, is_remote = parse_lever_location(j)
            
            jobs.append(Job(
                company       = company,
                external_id   = str(j["id"]),
                source_feed   = "Lever",
                title         = j["text"],
                countries     = countries,
                cities        = cities,
                is_remote     = is_remote,
                job_url       = j["hostedUrl"],
                apply_url     = j["applyUrl"],
                posted_at     = posted_at,
                job_updated_at= posted_at,
            ))
        logger.info("%s / %d jobs", company, len(jobs))
        return jobs