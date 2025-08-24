from __future__ import annotations

import re
from typing import List, Tuple, Set

# ── US States and Territories ──────────────────────────────────────────
_US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA", "HI", "IA", "ID", "IL",
    "IN", "KS", "KY", "LA", "MA", "MD", "ME", "MI", "MN", "MO", "MS", "MT", "NC", "ND", "NE",
    "NH", "NJ", "NM", "NV", "NY", "OH", "OK", "OR", "PA", "PR", "RI", "SC", "SD", "TN", "TX",
    "UT", "VA", "VT", "WA", "WI", "WV", "WY"
}

_US_STATE_NAMES = {
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado", "connecticut", 
    "delaware", "florida", "georgia", "hawaii", "idaho", "illinois", "indiana", "iowa", 
    "kansas", "kentucky", "louisiana", "maine", "maryland", "massachusetts", "michigan", 
    "minnesota", "mississippi", "missouri", "montana", "nebraska", "nevada", "new hampshire", 
    "new jersey", "new mexico", "new york", "north carolina", "north dakota", "ohio", 
    "oklahoma", "oregon", "pennsylvania", "rhode island", "south carolina", "south dakota", 
    "tennessee", "texas", "utah", "vermont", "virginia", "washington", "west virginia", 
    "wisconsin", "wyoming", "district of columbia", "puerto rico"
}

# ── City-States and Special Cases ──────────────────────────────────────
_CITY_STATES = {
    "singapore": ("Singapore", "Singapore"),
    "monaco": ("Monaco", "Monaco"),
    "vatican city": ("Vatican City", "Vatican City"),
    "san marino": ("San Marino", "San Marino"),
    "hong kong": ("Hong Kong", "Hong Kong"),
    "macau": ("Macau", "Macau"),
    "luxembourg": ("Luxembourg", "Luxembourg"),
}

# ── Comprehensive Global Countries for Tech Jobs ──────────────────────
_TECH_COUNTRIES = {
    # North America
    "united states", "usa", "us", "america", "united states of america",
    "canada", "mexico",
    
    # Europe - Major Tech Hubs
    "united kingdom", "uk", "england", "britain", "great britain", "scotland", "wales", "northern ireland",
    "germany", "deutschland", "france", "netherlands", "holland", "ireland", "switzerland", "sweden", 
    "norway", "denmark", "finland", "spain", "italy", "portugal", "austria", "belgium", "poland",
    "czech republic", "estonia", "latvia", "lithuania", "romania", "hungary", "bulgaria", "croatia",
    "slovakia", "slovenia", "greece", "ukraine", "belarus", "russia", "iceland", "luxembourg",
    "monaco", "san marino", "vatican city",
    
    # Asia-Pacific - Major Tech Centers
    "india", "china", "japan", "south korea", "singapore", "australia", "new zealand", "taiwan",
    "hong kong", "macau", "malaysia", "thailand", "philippines", "indonesia", "vietnam", "bangladesh",
    "sri lanka", "pakistan", "nepal", "myanmar", "cambodia", "laos", "brunei",
    
    # Middle East & Africa
    "israel", "united arab emirates", "uae", "emirates", "saudi arabia", "qatar", "kuwait", "oman",
    "bahrain", "egypt", "south africa", "nigeria", "kenya", "ghana", "morocco", "tunisia",
    "jordan", "lebanon", "turkey",
    
    # Latin America
    "brazil", "argentina", "chile", "colombia", "peru", "uruguay", "costa rica", "panama",
    "guatemala", "ecuador", "bolivia", "paraguay", "venezuela", "honduras", "nicaragua",
    "el salvador", "dominican republic", "puerto rico", "jamaica", "trinidad and tobago",
    
    # Other regions with growing tech scenes
    "mongolia", "kazakhstan", "uzbekistan", "kyrgyzstan", "tajikistan", "turkmenistan", 
    "afghanistan", "iran", "iraq", "yemen", "syria", "cyprus", "malta", "albania", 
    "montenegro", "serbia", "bosnia and herzegovina", "macedonia", "moldova", "georgia", 
    "armenia", "azerbaijan"
}

# ── Country Aliases and Variations ─────────────────────────────────────
_COUNTRY_ALIASES = {
    # English-speaking
    "usa": "United States",
    "us": "United States", 
    "america": "United States",
    "united states of america": "United States",
    "uk": "United Kingdom",
    "england": "United Kingdom",
    "britain": "United Kingdom",
    "great britain": "United Kingdom",
    "scotland": "United Kingdom",
    "wales": "United Kingdom",
    "northern ireland": "United Kingdom",
    
    # Europe
    "deutschland": "Germany",
    "holland": "Netherlands",
    
    # Asia
    "south korea": "South Korea",
    "north korea": "North Korea",
    
    # Middle East
    "uae": "United Arab Emirates",
    "emirates": "United Arab Emirates",
    
    # Special territories and city-states
    "hong kong": "Hong Kong",
    "macau": "Macau",
    "puerto rico": "Puerto Rico",
    "singapore": "Singapore",
    "monaco": "Monaco",
    "luxembourg": "Luxembourg",
}

# ── Remote Work Patterns ───────────────────────────────────────────────
_REMOTE_PATTERNS = [
    r"\bremote\b",
    r"\btelecommute\b", 
    r"\bwork\s+from\s+home\b",
    r"\bwfh\b",
    r"\banywhere\b",
    r"\bvirtual\b",
    r"\bdistributed\b",
    r"\bfrom\s+home\b"
]

_REMOTE_RE = re.compile("|".join(_REMOTE_PATTERNS), re.I)

def parse_greenhouse_location(raw: str) -> Tuple[List[str], List[str], bool]:
    """
    Parse Greenhouse location.name strings with comprehensive global country support.
    
    Handles patterns like:
    - "Singapore" (city-state)
    - "Germany" (country only)
    - "San Francisco, CA"
    - "New York, NY, United States" 
    - "London, United Kingdom"
    - "Remote"
    - "Remote - United States"
    - "San Francisco, CA | New York, NY"
    - "Multiple Locations"
    - "NY • United States"
    - "Berlin, Germany / London, UK"
    - "Tokyo, Japan"
    - "Bangalore, India"
    - "Toronto, Ontario, Canada"
    
    Returns: (cities, countries, is_remote)
    """
    if not raw or not raw.strip():
        return [], [], False
    
    raw = raw.strip()
    
    # ── 1) Handle remote cases ──────────────────────────────────────────
    if _REMOTE_RE.search(raw):
        countries = []
        
        # Look for country mentions after remote indicators
        remote_patterns = [
            r'remote\s*[-:(]\s*([^,|/)+]+)',
            r'remote\s+in\s+([^,|/]+)',
            r'remote\s*\|\s*([^,|/]+)',
            r'remote\s+([^,|/]+)'
        ]
        
        for pattern in remote_patterns:
            match = re.search(pattern, raw, re.I)
            if match:
                potential_country = match.group(1).strip()
                normalized = _normalize_country(potential_country)
                if normalized:
                    countries = [normalized]
                    break
        
        return [], countries, True
    
    # ── 2) Handle "Multiple Locations" or similar generic terms ─────────
    if re.search(r'\b(multiple|various|several|all)\s+(locations?|offices?|sites?|countries?)\b', raw, re.I):
        return [], [], False
    
    # ── 3) Parse on-site locations ─────────────────────────────────────
    cities: List[str] = []
    countries: Set[str] = set()
    
    # Split on common separators: |, /, ;, " or ", " and ", •
    location_chunks = re.split(r'\s*[|/;•]\s*|\s+(?:or|and)\s+', raw)
    
    for chunk in location_chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
            
        parsed_cities, parsed_countries = _parse_single_location(chunk)
        cities.extend(parsed_cities)
        countries.update(parsed_countries)
    
    return cities, list(countries), False

def _parse_single_location(location: str) -> Tuple[List[str], List[str]]:
    """Parse a single location string like 'San Francisco, CA, United States' or 'Singapore'"""
    cities: List[str] = []
    countries: List[str] = []
    
    # Handle bullet point and other separators
    for sep in ["•", "–", "—", " - ", " | "]:
        if sep in location:
            parts = [p.strip() for p in location.split(sep)]
            location = ", ".join(parts)
            break
    
    # Split by comma and clean up tokens
    tokens = [t.strip() for t in location.split(",") if t.strip()]
    
    if not tokens:
        return cities, countries
    
    # ── Handle single token case (e.g., "Singapore", "Germany") ─────────
    if len(tokens) == 1:
        token = tokens[0]
        token_lower = token.lower()
        
        # Check if it's a city-state (both city and country)
        if token_lower in _CITY_STATES:
            city_name, country_name = _CITY_STATES[token_lower]
            cities.append(city_name)
            countries.append(country_name)
        # Check if it's a known country
        elif _is_likely_country(token):
            normalized = _normalize_country(token)
            if normalized:
                countries.append(normalized)
        # Check if it's a US state (assume US)
        elif _is_us_state(token):
            cities.append(token)
            countries.append("United States")
        # Default: treat as city name
        else:
            cities.append(token)
        
        return cities, countries
    
    # ── Handle multi-token case ─────────────────────────────────────────
    # First token is usually the city
    potential_city = tokens[0]
    
    # Add first token as city unless it's obviously a country-only reference
    if not _is_country_only_reference(potential_city, tokens):
        cities.append(potential_city)
    
    # Process remaining tokens to identify countries and states
    for i, token in enumerate(tokens[1:], 1):
        # Check if it's a US state (postal code or full name)
        if _is_us_state(token):
            if "United States" not in countries:
                countries.append("United States")
        # Check if it's a country name or alias
        elif _is_likely_country(token):
            normalized = _normalize_country(token)
            if normalized and normalized not in countries:
                countries.append(normalized)
        # If it's the last token and we haven't identified a country yet,
        # it might be a country even if not in our known list
        elif i == len(tokens) - 1 and not countries:
            normalized = _normalize_country(token)
            if normalized:
                countries.append(normalized)
            else:
                # Fallback: treat as country name as-is if it looks like one
                if len(token) > 2 and re.match(r'^[a-zA-Z\s\-]+$', token):
                    countries.append(token.title())
    
    return cities, countries

def _is_country_only_reference(first_token: str, all_tokens: List[str]) -> bool:
    """Check if this appears to be a country-only reference (no city)"""
    # If there are multiple tokens and the first one is a known country,
    # it might be a "Germany, Berlin" type reference (reversed)
    if len(all_tokens) > 1 and _is_likely_country(first_token):
        # Check if the second token might be a city
        second_token = all_tokens[1]
        if not _is_likely_country(second_token) and not _is_us_state(second_token):
            return True
    return False

def _is_us_state(token: str) -> bool:
    """Check if token is a US state postal code or full name"""
    token_upper = token.upper()
    token_lower = token.lower()
    
    return (
        token_upper in _US_STATES or 
        token_lower in _US_STATE_NAMES or
        token.lower() in ["washington dc", "washington, dc", "district of columbia"]
    )

def _is_likely_country(token: str) -> bool:
    """Check if token is likely a country name"""
    token_lower = token.lower().strip()
    
    # Check if it's in our comprehensive tech countries list
    if token_lower in _TECH_COUNTRIES:
        return True
    
    # Check if it's a known US state (not a country)
    if _is_us_state(token):
        return False
    
    # Check for common country patterns
    country_suffixes = ["land", "stan", "burg", "mark", "ia", "nia", "gal", "way"]
    if any(token_lower.endswith(suffix) for suffix in country_suffixes):
        return True
    
    # Check for multi-word countries
    multi_word_indicators = ["republic", "kingdom", "emirates", "states", "islands", "federation"]
    if any(indicator in token_lower for indicator in multi_word_indicators):
        return True
    
    return False

def _normalize_country(country: str) -> str:
    """Normalize country name using aliases and proper casing"""
    if not country:
        return ""
    
    country_lower = country.lower().strip()
    
    # Remove common prefixes/suffixes that might interfere
    country_lower = re.sub(r'^\s*(the\s+|republic\s+of\s+)?', '', country_lower)
    country_lower = re.sub(r'\s*[\(\)]\s*.*$', '', country_lower)  # Remove parenthetical
    
    # Check aliases first
    if country_lower in _COUNTRY_ALIASES:
        return _COUNTRY_ALIASES[country_lower]
    
    # Check if it's in our comprehensive tech countries list
    if country_lower in _TECH_COUNTRIES:
        # Return proper title case
        return country.strip().title()
    
    # Handle special multi-word cases
    special_cases = {
        "new zealand": "New Zealand",
        "south africa": "South Africa",
        "south korea": "South Korea", 
        "north korea": "North Korea",
        "costa rica": "Costa Rica",
        "puerto rico": "Puerto Rico",
        "united arab emirates": "United Arab Emirates",
        "saudi arabia": "Saudi Arabia",
        "czech republic": "Czech Republic",
        "dominican republic": "Dominican Republic",
        "sri lanka": "Sri Lanka",
        "hong kong": "Hong Kong",
        "new york": "United States",  # Common misparse
        "california": "United States",
        "texas": "United States"
    }
    
    if country_lower in special_cases:
        return special_cases[country_lower]
    
    # Default: title case the country name if it looks valid
    if len(country.strip()) > 2 and re.match(r'^[a-zA-Z\s\-]+$', country.strip()):
        return country.strip().title()
    
    return "" 