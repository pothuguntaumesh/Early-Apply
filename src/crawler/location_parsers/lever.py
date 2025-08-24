from __future__ import annotations

import re
from typing import List, Tuple, Dict, Any, Optional

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

# ── Country Code Mappings ──────────────────────────────────────────────
_COUNTRY_CODE_TO_NAME = {
    "US": "United States", "CA": "Canada", "GB": "United Kingdom", "UK": "United Kingdom",
    "DE": "Germany", "FR": "France", "NL": "Netherlands", "ES": "Spain", "IT": "Italy",
    "SE": "Sweden", "NO": "Norway", "DK": "Denmark", "FI": "Finland", "CH": "Switzerland",
    "AT": "Austria", "BE": "Belgium", "IE": "Ireland", "PL": "Poland", "CZ": "Czech Republic",
    "HU": "Hungary", "RO": "Romania", "BG": "Bulgaria", "HR": "Croatia", "SI": "Slovenia",
    "SK": "Slovakia", "EE": "Estonia", "LV": "Latvia", "LT": "Lithuania", "IS": "Iceland",
    "GR": "Greece", "TR": "Turkey", "IL": "Israel", "AE": "United Arab Emirates",
    "SA": "Saudi Arabia", "EG": "Egypt", "ZA": "South Africa", "NG": "Nigeria", "KE": "Kenya",
    "BR": "Brazil", "AR": "Argentina", "CL": "Chile", "CO": "Colombia", "MX": "Mexico",
    "JP": "Japan", "KR": "South Korea", "CN": "China", "IN": "India", "SG": "Singapore",
    "AU": "Australia", "NZ": "New Zealand", "TW": "Taiwan", "HK": "Hong Kong", "MY": "Malaysia",
    "TH": "Thailand", "PH": "Philippines", "ID": "Indonesia", "VN": "Vietnam", "RU": "Russia",
    "UA": "Ukraine", "LU": "Luxembourg", "PT": "Portugal"
}

# ── Remote Work Patterns ───────────────────────────────────────────────
_REMOTE_PATTERNS = [
    r"\bremote\b", r"\btelecommute\b", r"\bwork\s+from\s+home\b", 
    r"\bwfh\b", r"\banywhere\b", r"\bvirtual\b", r"\bdistributed\b"
]

_REMOTE_RE = re.compile("|".join(_REMOTE_PATTERNS), re.I)

def parse_lever_location(job_data: Dict[str, Any]) -> Tuple[List[str], List[str], bool]:
    """
    Parse Lever location data which includes categories.location, categories.allLocations, 
    country code, and workplaceType.
    
    Args:
        job_data: The job dictionary containing categories, country, and workplaceType
        
    Returns: (cities, countries, is_remote)
    """
    cities: List[str] = []
    countries: List[str] = []
    is_remote = False
    
    # Check workplace type for remote work
    workplace_type = job_data.get("workplaceType", "").lower()
    is_remote = workplace_type == "remote"
    
    # Get categories object
    categories = job_data.get("categories", {})
    
    # Parse primary location
    primary_location = categories.get("location", "")
    if primary_location:
        parsed_cities, parsed_countries = _parse_location_string(primary_location)
        cities.extend(parsed_cities)
        countries.extend(parsed_countries)
    
    # Parse all locations array
    all_locations = categories.get("allLocations", [])
    for location in all_locations:
        if location and location != primary_location:  # Avoid duplicates
            parsed_cities, parsed_countries = _parse_location_string(location)
            for city in parsed_cities:
                if city not in cities:
                    cities.append(city)
            for country in parsed_countries:
                if country not in countries:
                    countries.append(country)
    
    # Add country from country code if not already present
    country_code = job_data.get("country", "")
    if country_code:
        normalized_country = _normalize_country_code(country_code)
        if normalized_country and normalized_country not in countries:
            countries.append(normalized_country)
    
    # If no locations found but we have a country, use that
    if not cities and not countries and country_code:
        normalized_country = _normalize_country_code(country_code)
        if normalized_country:
            countries.append(normalized_country)
    
    return cities, countries, is_remote

def _parse_location_string(location: str) -> Tuple[List[str], List[str]]:
    """
    Parse a location string like 'Seattle, WA', 'New York', 'United States'.
    
    Args:
        location: Location string to parse
        
    Returns: (cities, countries)
    """
    if not location or not location.strip():
        return [], []
    
    location = location.strip()
    
    # Check if it's a remote location
    if _REMOTE_RE.search(location):
        # Try to extract country from remote location string
        countries = []
        remote_patterns = [
            r'remote\s*[-:(]\s*([^,|/)+]+)',
            r'remote\s+in\s+([^,|/]+)',
            r'remote\s*\|\s*([^,|/]+)',
            r'remote\s+([^,|/]+)'
        ]
        
        for pattern in remote_patterns:
            match = re.search(pattern, location, re.I)
            if match:
                potential_country = match.group(1).strip()
                normalized = _normalize_country(potential_country)
                if normalized:
                    countries = [normalized]
                    break
        
        return [], countries
    
    # Split on common separators
    parts = [part.strip() for part in re.split(r'[,;|]', location) if part.strip()]
    
    if not parts:
        return [], []
    
    cities = []
    countries = []
    
    # Check if it's just a country
    if len(parts) == 1:
        single_part = parts[0]
        normalized_country = _normalize_country(single_part)
        if normalized_country:
            countries.append(normalized_country)
        else:
            # Assume it's a city and try to infer country
            cities.append(single_part)
            inferred_country = _infer_country_from_city(single_part)
            if inferred_country:
                countries.append(inferred_country)
    else:
        # Multiple parts - likely "City, State" or "City, Country"
        potential_city = parts[0]
        cities.append(potential_city)
        
        # Check if second part is a US state
        if len(parts) >= 2:
            second_part = parts[1].strip()
            if _is_us_state(second_part):
                countries.append("United States")
            else:
                # Try to normalize as country
                normalized_country = _normalize_country(second_part)
                if normalized_country:
                    countries.append(normalized_country)
                else:
                    # Infer country from city
                    inferred_country = _infer_country_from_city(potential_city)
                    if inferred_country:
                        countries.append(inferred_country)
        
        # If there's a third part, it might be a country (like "City, State, Country")
        if len(parts) >= 3:
            third_part = parts[2].strip()
            normalized_country = _normalize_country(third_part)
            if normalized_country and normalized_country not in countries:
                countries.append(normalized_country)
    
    return cities, countries

def _is_us_state(token: str) -> bool:
    """Check if a token is a US state abbreviation or name."""
    if not token:
        return False
    
    token_upper = token.upper().strip()
    token_lower = token.lower().strip()
    
    return token_upper in _US_STATES or token_lower in _US_STATE_NAMES

def _normalize_country_code(country_code: str) -> Optional[str]:
    """Convert country code to full country name."""
    if not country_code:
        return None
    
    return _COUNTRY_CODE_TO_NAME.get(country_code.upper())

def _normalize_country(country: str) -> Optional[str]:
    """Normalize country name to a standard format."""
    if not country:
        return None
    
    country = country.strip()
    country_lower = country.lower()
    
    # Direct mappings for common variations
    country_mappings = {
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
        "deutschland": "Germany",
        "holland": "Netherlands",
        "south korea": "South Korea",
        "uae": "United Arab Emirates",
        "emirates": "United Arab Emirates",
        "hong kong": "Hong Kong",
        "singapore": "Singapore",
        "puerto rico": "Puerto Rico",
    }
    
    # Check direct mappings first
    if country_lower in country_mappings:
        return country_mappings[country_lower]
    
    # If not found, return title case version if it looks like a valid country
    if len(country) >= 3 and country.replace(" ", "").isalpha():
        return country.title()
    
    return None

def _infer_country_from_city(city: str) -> Optional[str]:
    """
    Try to infer country from major tech hub cities.
    """
    if not city:
        return None
    
    city_lower = city.lower().strip()
    
    # Major tech hub cities - focused list
    tech_hubs = {
        # US Major Tech Cities
        "seattle": "United States", "san francisco": "United States", "new york": "United States",
        "boston": "United States", "chicago": "United States", "austin": "United States",
        "denver": "United States", "atlanta": "United States", "los angeles": "United States",
        "portland": "United States", "miami": "United States", "dallas": "United States",
        "houston": "United States", "phoenix": "United States", "philadelphia": "United States",
        "detroit": "United States", "minneapolis": "United States", "raleigh": "United States",
        "san diego": "United States", "san jose": "United States", "palo alto": "United States",
        "mountain view": "United States", "sunnyvale": "United States", "cupertino": "United States",
        "redmond": "United States", "bellevue": "United States", "santa clara": "United States",
        "oakland": "United States", "berkeley": "United States", "nashville": "United States",
        
        # Europe Major Tech Cities
        "london": "United Kingdom", "manchester": "United Kingdom", "edinburgh": "United Kingdom",
        "dublin": "Ireland", "berlin": "Germany", "munich": "Germany", "hamburg": "Germany",
        "paris": "France", "amsterdam": "Netherlands", "stockholm": "Sweden", "copenhagen": "Denmark",
        "oslo": "Norway", "helsinki": "Finland", "zurich": "Switzerland", "vienna": "Austria",
        "brussels": "Belgium", "madrid": "Spain", "barcelona": "Spain", "rome": "Italy",
        "milan": "Italy", "lisbon": "Portugal", "warsaw": "Poland", "prague": "Czech Republic",
        "budapest": "Hungary", "bucharest": "Romania", "sofia": "Bulgaria", "zagreb": "Croatia",
        "tallinn": "Estonia", "riga": "Latvia", "vilnius": "Lithuania", "athens": "Greece",
        "istanbul": "Turkey",
        
        # Asia-Pacific Major Tech Cities
        "tokyo": "Japan", "osaka": "Japan", "seoul": "South Korea", "busan": "South Korea",
        "beijing": "China", "shanghai": "China", "shenzhen": "China", "guangzhou": "China",
        "hangzhou": "China", "mumbai": "India", "bangalore": "India", "delhi": "India",
        "hyderabad": "India", "chennai": "India", "pune": "India", "singapore": "Singapore",
        "sydney": "Australia", "melbourne": "Australia", "brisbane": "Australia", "perth": "Australia",
        "auckland": "New Zealand", "wellington": "New Zealand", "taipei": "Taiwan", "hong kong": "Hong Kong",
        "kuala lumpur": "Malaysia", "bangkok": "Thailand", "manila": "Philippines", "jakarta": "Indonesia",
        "ho chi minh city": "Vietnam", "hanoi": "Vietnam",
        
        # Canada Major Tech Cities
        "toronto": "Canada", "vancouver": "Canada", "montreal": "Canada", "ottawa": "Canada",
        "calgary": "Canada", "edmonton": "Canada",
        
        # Middle East & Others
        "tel aviv": "Israel", "jerusalem": "Israel", "dubai": "United Arab Emirates",
        "abu dhabi": "United Arab Emirates", "riyadh": "Saudi Arabia", "cairo": "Egypt",
        "cape town": "South Africa", "johannesburg": "South Africa", "lagos": "Nigeria",
        "nairobi": "Kenya", "buenos aires": "Argentina", "santiago": "Chile", "bogota": "Colombia",
        "lima": "Peru", "montevideo": "Uruguay", "san jose": "Costa Rica", "mexico city": "Mexico",
        
        # Eastern Europe & Russia
        "moscow": "Russia", "saint petersburg": "Russia", "kyiv": "Ukraine", "minsk": "Belarus"
    }
    
    return tech_hubs.get(city_lower) 