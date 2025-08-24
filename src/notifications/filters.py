from src.crawler.models import JobRecord
from src.notifications.models import UserJobPref
import logging
import re

log = logging.getLogger(__name__)

CITY_TO_COUNTRY = {
    "new york": "united states",
    "san francisco": "united states",
    "london": "united kingdom",
    "berlin": "germany",
    "bangalore": "india",
    "hyderabad": "india",
    "toronto": "canada",
    "vancouver": "canada",
    "sydney": "australia",
    "paris": "france",
    "mexico city": "mexico",
    "warszawa": "poland",
    "belgrade": "serbia",
    "madrid": "spain",
    "trion building": "united kingdom",
    "montreal": "canada",
    "kyiv": "ukraine",
    "são paulo": "brazil",
    "aarhus": "denmark",
    "amsterdam": "netherlands",
    "hybrid": "united states",
    "in-office": "united states",
    "paris area": "france",
    "china": "china",
    "greater toronto area": "canada",
    "toronto, ontario": "canada",
    "greater toronto area, ontario": "canada",
    "krakow": "poland",
    "lisbon": "portugal",
    "montpellier": "france",
    "sophia antipolis": "france",
    "bordeaux": "france",
    "grenoble": "france",
    "lyon": "france",
    "nantes": "france",
    "dublin": "ireland",
    "dublin, ireland": "ireland",
    "flexible": "remote",
    "ottawa": "canada",
    "seoul": "south korea",
    "oslo": "norway",
    "copenhagen": "denmark",
    "dubai": "united arab emirates",
    "abu dhabi": "united arab emirates",
    "vilnius": "lithuania",
    "stockholm": "sweden",
    "tokyo": "japan",
    "tokyo, japan": "japan",
    "cr-san jose": "costa rica",
    "san josé": "costa rica",
    "pl-warsaw": "poland",
    "warsaw": "poland",
    "mso": "remote",
    "herzliya": "israel",
    "seville": "spain",
    "chennai": "india",
    "geneva": "switzerland",
    "edinburgh": "united kingdom",
    "edinburgh, united kingdom": "united kingdom",
    "tel aviv": "israel",
}

COMMON_COUNTRY_ALIASES = {
    "us": "united states",
    "usa": "united states",
    "u.s.": "united states",
    "uk": "united kingdom",
    "u.k.": "united kingdom",
    "gb": "united kingdom",
    "uae": "united arab emirates",
    "ca": "canada",
    "de": "germany",
}

SENIOR_KEYWORDS = {
    "senior",
    "sr",
    "sr.",
    "staff",
    "lead",
    "principal",
    "architect",
    "director",
    "manager",
    "vp",
    "head",
    "chief",
    "executive",
}

ROMAN_LVLS = {"iii", "iv", "v", "vi"}
DIGIT_LVLS = {"3", "4", "5", "6", "7", "8", "9"}

TOKEN_RE = re.compile(r"[a-z0-9]+")


def normalize_location(name: str) -> str:
    name = name.lower().strip()
    return COMMON_COUNTRY_ALIASES.get(name, name)


def match_country(job: JobRecord, pref: UserJobPref) -> bool:
    preferred_countries = {normalize_location(c) for c in (pref.countries or [])}
    job_countries = {normalize_location(c) for c in (job.countries or [])}
    job_cities = {c.lower().strip() for c in (job.cities or [])}
    if job_countries & preferred_countries:
        return True
    inferred = {normalize_location(CITY_TO_COUNTRY[city]) for city in job_cities if city in CITY_TO_COUNTRY}
    for city in job_cities - set(CITY_TO_COUNTRY):
        log.warning(f"City not mapped to country: {city}")
    if inferred & preferred_countries:
        return True
    for pc in preferred_countries:
        for jc in job_countries:
            if pc in jc or jc in pc:
                return True
        for city in job_cities:
            if pc in city or city in pc:
                return True
    return False


def is_senior_level(title: str) -> bool:
    tokens = set(TOKEN_RE.findall(title.lower()))
    if tokens & SENIOR_KEYWORDS:
        return True
    if tokens & ROMAN_LVLS:
        return True
    if any(t in DIGIT_LVLS and len(t) == 1 for t in tokens):
        return True
    return False


def get_job_level(job: JobRecord) -> str:
    return "senior" if is_senior_level(job.title) else "entry"


def match_job(job: JobRecord, pref: UserJobPref) -> bool:
    job_level = get_job_level(job)
    if job_level not in [lvl.lower() for lvl in pref.levels]:
        return False
    if not match_country(job, pref):
        return False
    return True
