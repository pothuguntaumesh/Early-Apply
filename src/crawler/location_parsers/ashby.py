from __future__ import annotations

import re
from typing import List, Tuple, Dict, Any, Optional

def parse_ashby_location(job_data: Dict[str, Any]) -> Tuple[List[str], List[str], bool]:
    """
    Parse Ashby location data which includes primary location, address, and secondaryLocations.
    
    Handles patterns like:
    - Primary location: "US-CA-Dublin", "US-WA-Bellevue", etc.
    - Simple location: "Seattle", "London", etc.
    - Direct address field with postalAddress
    - Secondary locations with detailed address objects
    
    Args:
        job_data: The job dictionary containing location, address, and/or secondaryLocations
        
    Returns: (cities, countries, is_remote)
    """
    cities: List[str] = []
    countries: List[str] = []
    is_remote = False
    
    # Check if job is marked as remote
    is_remote = job_data.get("isRemote", False) or job_data.get("is_remote", False)
    
    # Parse primary location string
    primary_location = job_data.get("location", "")
    if primary_location:
        city, country = _parse_location_string(primary_location)
        if city:
            cities.append(city)
        if country:
            countries.append(country)
    
    # Parse direct address field
    address = job_data.get("address", {})
    if address:
        city, country = _parse_address_object(address)
        if city and city not in cities:
            cities.append(city)
        if country and country not in countries:
            countries.append(country)
    
    # Parse secondary locations
    secondary_locations = job_data.get("secondaryLocations", [])
    for secondary in secondary_locations:
        # Try location string first
        location_str = secondary.get("location", "")
        if location_str:
            city, country = _parse_location_string(location_str)
            if city and city not in cities:
                cities.append(city)
            if country and country not in countries:
                countries.append(country)
        
        # Also check address object for more details
        secondary_address = secondary.get("address", {})
        if secondary_address:
            city, country = _parse_address_object(secondary_address)
            if city and city not in cities:
                cities.append(city)
            if country and country not in countries:
                countries.append(country)
    
    return cities, countries, is_remote

def _parse_address_object(address: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse address object with postalAddress.
    
    Args:
        address: Address object containing postalAddress
        
    Returns: (city, country)
    """
    postal_address = address.get("postalAddress", {})
    if not postal_address:
        return None, None
    
    city = postal_address.get("addressLocality")
    country = postal_address.get("addressCountry")
    
    # Normalize country name
    if country:
        country = _normalize_country(country)
    
    return city, country

def _parse_location_string(location: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse location strings like:
    - "US-CA-Dublin", "US-WA-Bellevue" (formatted)
    - "Seattle", "London", "New York" (simple city names)
    
    Returns: (city, country)
    """
    if not location or not location.strip():
        return None, None
    
    location = location.strip()
    
    # Handle format like "US-CA-Dublin"
    parts = location.split("-")
    if len(parts) >= 3:
        country_code = parts[0]
        # state_code = parts[1]  # We could use this if needed
        city = "-".join(parts[2:])  # Join remaining parts as city name
        
        country = _normalize_country_code(country_code)
        return city, country
    
    # Handle simple city names like "Seattle", "London", etc.
    # Try to infer country from well-known cities
    city = location
    country = _infer_country_from_city(city)
    
    return city, country

def _infer_country_from_city(city: str) -> Optional[str]:
    """
    Try to infer country from well-known city names.
    This is a best-effort approach for common tech hub cities.
    """
    if not city:
        return None
    
    city_lower = city.lower().strip()
    
    # Major US cities
    us_cities = {
        "seattle", "san francisco", "new york", "boston", "chicago", "austin", "denver",
        "atlanta", "los angeles", "portland", "miami", "dallas", "houston", "phoenix",
        "philadelphia", "detroit", "minneapolis", "kansas city", "nashville", "raleigh",
        "sacramento", "san diego", "san jose", "palo alto", "mountain view", "sunnyvale",
        "cupertino", "redmond", "bellevue", "santa clara", "fremont", "oakland", "berkeley"
    }
    
    # Major international cities
    international_cities = {
        "london": "United Kingdom",
        "manchester": "United Kingdom", 
        "edinburgh": "United Kingdom",
        "dublin": "Ireland",
        "berlin": "Germany",
        "munich": "Germany",
        "hamburg": "Germany",
        "paris": "France",
        "amsterdam": "Netherlands",
        "stockholm": "Sweden",
        "copenhagen": "Denmark",
        "oslo": "Norway",
        "helsinki": "Finland",
        "zurich": "Switzerland",
        "geneva": "Switzerland",
        "vienna": "Austria",
        "brussels": "Belgium",
        "madrid": "Spain",
        "barcelona": "Spain",
        "rome": "Italy",
        "milan": "Italy",
        "lisbon": "Portugal",
        "warsaw": "Poland",
        "prague": "Czech Republic",
        "budapest": "Hungary",
        "bucharest": "Romania",
        "sofia": "Bulgaria",
        "zagreb": "Croatia",
        "ljubljana": "Slovenia",
        "bratislava": "Slovakia",
        "tallinn": "Estonia",
        "riga": "Latvia",
        "vilnius": "Lithuania",
        "reykjavik": "Iceland",
        "athens": "Greece",
        "istanbul": "Turkey",
        "tel aviv": "Israel",
        "jerusalem": "Israel",
        "dubai": "United Arab Emirates",
        "abu dhabi": "United Arab Emirates",
        "riyadh": "Saudi Arabia",
        "cairo": "Egypt",
        "cape town": "South Africa",
        "johannesburg": "South Africa",
        "lagos": "Nigeria",
        "nairobi": "Kenya",
        "buenos aires": "Argentina",
        "santiago": "Chile",
        "bogota": "Colombia",
        "lima": "Peru",
        "montevideo": "Uruguay",
        "san jose": "Costa Rica",
        "toronto": "Canada",
        "vancouver": "Canada",
        "montreal": "Canada",
        "ottawa": "Canada",
        "calgary": "Canada",
        "edmonton": "Canada",
        "tokyo": "Japan",
        "osaka": "Japan",
        "kyoto": "Japan",
        "seoul": "South Korea",
        "busan": "South Korea",
        "singapore": "Singapore",
        "sydney": "Australia",
        "melbourne": "Australia",
        "brisbane": "Australia",
        "perth": "Australia",
        "auckland": "New Zealand",
        "wellington": "New Zealand",
        "bangalore": "India",
        "mumbai": "India",
        "delhi": "India",
        "hyderabad": "India",
        "chennai": "India",
        "pune": "India",
        "kolkata": "India",
        "beijing": "China",
        "shanghai": "China",
        "shenzhen": "China",
        "guangzhou": "China",
        "hangzhou": "China",
        "nanjing": "China",
        "taipei": "Taiwan",
        "hong kong": "Hong Kong",
        "kuala lumpur": "Malaysia",
        "bangkok": "Thailand",
        "manila": "Philippines",
        "jakarta": "Indonesia",
        "ho chi minh city": "Vietnam",
        "hanoi": "Vietnam",
        "dhaka": "Bangladesh",
        "colombo": "Sri Lanka",
        "karachi": "Pakistan",
        "lahore": "Pakistan",
        "islamabad": "Pakistan"
    }
    
    if city_lower in us_cities:
        return "United States"
    
    return international_cities.get(city_lower)

def _normalize_country_code(country_code: str) -> str:
    """Convert country codes to full country names."""
    country_mapping = {
        "US": "United States",
        "CA": "Canada", 
        "GB": "United Kingdom",
        "UK": "United Kingdom",
        "DE": "Germany",
        "FR": "France",
        "AU": "Australia",
        "IN": "India",
        "SG": "Singapore",
        "JP": "Japan",
        "CN": "China",
        "BR": "Brazil",
        "MX": "Mexico",
        "NL": "Netherlands",
        "SE": "Sweden",
        "NO": "Norway",
        "DK": "Denmark",
        "FI": "Finland",
        "CH": "Switzerland",
        "AT": "Austria",
        "BE": "Belgium",
        "IE": "Ireland",
        "IT": "Italy",
        "ES": "Spain",
        "PT": "Portugal",
        "PL": "Poland",
        "CZ": "Czech Republic",
        "HU": "Hungary",
        "RO": "Romania",
        "BG": "Bulgaria",
        "HR": "Croatia",
        "SI": "Slovenia",
        "SK": "Slovakia",
        "EE": "Estonia",
        "LV": "Latvia",
        "LT": "Lithuania",
        "IS": "Iceland",
        "GR": "Greece",
        "TR": "Turkey",
        "IL": "Israel",
        "AE": "United Arab Emirates",
        "SA": "Saudi Arabia",
        "EG": "Egypt",
        "ZA": "South Africa",
        "NG": "Nigeria",
        "KE": "Kenya",
        "AR": "Argentina",
        "CL": "Chile",
        "CO": "Colombia",
        "PE": "Peru",
        "UY": "Uruguay",
        "CR": "Costa Rica",
        "KR": "South Korea",
        "TW": "Taiwan",
        "HK": "Hong Kong",
        "MY": "Malaysia",
        "TH": "Thailand",
        "PH": "Philippines",
        "ID": "Indonesia",
        "VN": "Vietnam",
        "BD": "Bangladesh",
        "LK": "Sri Lanka",
        "PK": "Pakistan",
        "NZ": "New Zealand",
    }
    
    return country_mapping.get(country_code.upper(), country_code)

def _normalize_country(country: str) -> str:
    """Normalize country names to standard format."""
    if not country:
        return ""
    
    country = country.strip()
    
    # Common mappings
    country_aliases = {
        "USA": "United States",
        "US": "United States",
        "America": "United States", 
        "United States of America": "United States",
        "UK": "United Kingdom",
        "England": "United Kingdom",
        "Britain": "United Kingdom",
        "Great Britain": "United Kingdom",
        "UAE": "United Arab Emirates",
        "Emirates": "United Arab Emirates",
    }
    
    return country_aliases.get(country, country) 