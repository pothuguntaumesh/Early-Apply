import re, aiohttp, logging
from datetime import datetime, timezone
from typing import List

from src.crawler.adapters.base import Adapter
from src.crawler.schemas import Job

logger = logging.getLogger("Workday")
ISO_TS = "%Y-%m-%dT%H:%M:%S%z"          # 2025-06-28T14:09:23Z
ISO_TS_MS = "%Y-%m-%dT%H:%M:%S.%f%z"    # 2025-06-28T14:09:23.456Z


class WorkdayAdapter(Adapter):
    # ─────────────────────────────────────────────────────────
    async def fetch_jobs(self, company: str, url: str) -> List[Job]:
        if self._is_legacy_url(url):
            return await self._fetch_legacy_jobs(company, url)
        return await self._fetch_new_jobs(company, url)   # (to-do)

    def _is_legacy_url(self, url: str) -> bool:
        return "/wday/cxs/" in url or "graph" not in url.lower()

    # ─────────────────────────────────────────────────────────
    async def _fetch_legacy_jobs(self, company: str, landing_url: str) -> List[Job]:
        """
        1. Derive the real list endpoint:
           https://{tenant}.{dc}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs
        2. POST page=1..N, pageSize=50
        3. Map each entry in `jobPostings` → Job  (no extra detail call)
        """
        tenant, dc = re.match(r"https://([^.]*)\.(wd\d)\.", landing_url).groups()
        site_slug  = landing_url.rstrip("/").split("/")[-1]

        list_url   = (
            f"https://{tenant}.{dc}.myworkdayjobs.com/"
            f"wday/cxs/{tenant}/{site_slug}/jobs"
        )

        jobs: List[Job] = []
        page, page_size = 1, 50

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        ) as session:
            while True:
                body = {
                    "appliedFacets": {},
                    "searchText": "",
                    "searchRequest": {"searchText": ""},
                    "page": page,
                    "pageSize": page_size,
                }
                async with session.post(
                    list_url,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                        "Origin": f"https://{tenant}.{dc}.myworkdayjobs.com",
                        "Referer": landing_url,
                    },
                    json=body,
                ) as resp:
                    resp.raise_for_status()
                    payload = await resp.json()

                postings = payload.get("jobPostings", [])
                if not postings:
                    break  # no more pages

                for p in postings:
                    # Workday’s list JSON wraps the actual data in "jobPosting"
                    jp = p.get("jobPosting", p)  # some tenants flatten
                    job_id = (
                        jp.get("jobPostingId")
                        or next(iter(jp.get("bulletFields", [])), None)
                    )
                    if not job_id:  # skip malformed rows
                        continue

                    title = jp.get("title", "").strip()

                    # posted date parsing
                    raw_posted = jp.get("postedOn") or jp.get("startDate") or ""
                    posted_at = _parse_ts(raw_posted)

                    # URL (externalPath starts with '/job/...')
                    ext_path = jp.get("externalPath") or f"/job/{job_id}"
                    job_url  = f"https://{tenant}.{dc}.myworkdayjobs.com{ext_path}"

                    # locations: if Workday gives "locationsText" only, keep it in cities
                    loc_text = jp.get("locationsText", "")
                    cities   = [loc_text] if loc_text else []
                    countries = []
                    is_remote = "remote" in loc_text.lower()

                    jobs.append(
                        Job(
                            company=company,
                            external_id=str(job_id),
                            source_feed="Workday",
                            title=title,
                            countries=countries,
                            cities=cities,
                            is_remote=is_remote,
                            job_url=job_url,
                            apply_url=job_url,
                            posted_at=posted_at,
                            job_updated_at=posted_at,
                        )
                    )

                page += 1  

        logger.info("%s – %d legacy jobs", company, len(jobs))
        return jobs


# ─────────── ts helper ───────────
def _parse_ts(raw: str) -> datetime:
    """
    Workday list feed gives:
        • ISO with Z     2025-06-28T14:09:23Z
        • ISO with ms    2025-06-28T14:09:23.456Z
        • Friendly text  "Posted Today" / "Posted Yesterday" – fallback to now()
    """
    if not raw:
        return datetime.now(timezone.utc)

    iso = raw.replace("Z", "+00:00")
    for fmt in (ISO_TS_MS, ISO_TS):
        try:
            return datetime.strptime(iso, fmt).astimezone(timezone.utc)
        except ValueError:
            continue
    return datetime.now(timezone.utc)
