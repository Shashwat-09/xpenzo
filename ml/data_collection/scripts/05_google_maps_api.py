"""
Google Maps Places API Scraper (Free Tier)
Uses Google Maps Places API to fetch business names and categories.

Free tier: 28,000 requests/month ($200 free credit)
  - Nearby Search: 32 calls × 20 results = 640 businesses per city
  - Text Search: focused queries per category

Dependencies: pip install requests tqdm
Setup: Get API key from https://console.cloud.google.com/apis/credentials
       Enable "Places API" and "Maps JavaScript API"
       Set env variable: GOOGLE_MAPS_API_KEY=your_key_here

Output: CSV in processed/google_maps_businesses.csv
"""

import os
import csv
import json
import time
import requests
from pathlib import Path
from collections import defaultdict
from typing import Any

SCRIPT_DIR = Path(__file__).parent
RAW_DIR = SCRIPT_DIR.parent / "raw" / "google_maps"
OUTPUT_DIR = SCRIPT_DIR.parent / "processed"

# Google Maps Places API endpoints
NEARBY_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

# City centers (lat, lng) for Nearby Search
CITY_COORDS = {
    "mumbai": (19.0760, 72.8777),
    "delhi": (28.6139, 77.2090),
    "bangalore": (12.9716, 77.5946),
    "hyderabad": (17.3850, 78.4867),
    "chennai": (13.0827, 80.2707),
    "kolkata": (22.5726, 88.3639),
    "pune": (18.5204, 73.8567),
    "ahmedabad": (23.0225, 72.5714),
    "jaipur": (26.9124, 75.7873),
    "lucknow": (26.8467, 80.9462),
    "chandigarh": (30.7333, 76.7794),
    "indore": (22.7196, 75.8577),
    "bhopal": (23.2599, 77.4126),
    "nagpur": (21.1458, 79.0882),
    "kochi": (9.9312, 76.2673),
    "coimbatore": (11.0168, 76.9558),
    "surat": (21.1702, 72.8311),
    "patna": (25.6093, 85.1376),
    "guwahati": (26.1445, 91.7362),
    "bhubaneswar": (20.2961, 85.8245),
}

# Business types supported by Google Places API
PLACE_TYPES = [
    # Food & Dining
    "restaurant", "cafe", "bakery", "bar", "meal_delivery", "meal_takeaway",
    # Shopping
    "clothing_store", "electronics_store", "jewelry_store", "shoe_store",
    "book_store", "furniture_store", "hardware_store", "pet_store",
    "shopping_mall", "department_store", "supermarket", "convenience_store",
    "florist", "gift_shop",
    # Healthcare
    "hospital", "pharmacy", "dentist", "doctor", "veterinary_care",
    # Finance
    "bank", "atm", "insurance_agency", "accounting",
    # Transportation
    "gas_station", "car_dealer", "car_repair", "car_wash", "car_rental",
    # Education
    "school", "university",
    # Entertainment
    "movie_theater", "museum", "amusement_park", "aquarium", "zoo",
    "bowling_alley", "night_club",
    # Services
    "beauty_salon", "hair_care", "spa", "gym", "laundry",
    "locksmith", "painter", "plumber", "electrician",
    # Travel
    "lodging", "travel_agency",
    # Religious
    "hindu_temple", "mosque", "church",
]

# Map Google place types to our L1 categories
GOOGLE_TYPE_TO_L1 = {
    "restaurant": "Food & Dining", "cafe": "Food & Dining",
    "bakery": "Food & Dining", "bar": "Food & Dining",
    "meal_delivery": "Food & Dining", "meal_takeaway": "Food & Dining",
    "clothing_store": "Shopping", "electronics_store": "Shopping",
    "jewelry_store": "Shopping", "shoe_store": "Shopping",
    "book_store": "Shopping", "furniture_store": "Shopping",
    "hardware_store": "Shopping", "pet_store": "Shopping",
    "shopping_mall": "Shopping", "department_store": "Shopping",
    "supermarket": "Shopping", "convenience_store": "Shopping",
    "florist": "Shopping", "gift_shop": "Shopping",
    "hospital": "Healthcare", "pharmacy": "Healthcare",
    "dentist": "Healthcare", "doctor": "Healthcare",
    "veterinary_care": "Healthcare",
    "bank": "Finance", "atm": "Finance",
    "insurance_agency": "Finance", "accounting": "Finance",
    "gas_station": "Transportation", "car_dealer": "Transportation",
    "car_repair": "Transportation", "car_wash": "Transportation",
    "car_rental": "Transportation",
    "school": "Education", "university": "Education",
    "movie_theater": "Entertainment", "museum": "Entertainment",
    "amusement_park": "Entertainment", "aquarium": "Entertainment",
    "zoo": "Entertainment", "bowling_alley": "Entertainment",
    "night_club": "Entertainment",
    "beauty_salon": "Services", "hair_care": "Services",
    "spa": "Fitness & Wellness", "gym": "Fitness & Wellness",
    "laundry": "Services", "locksmith": "Services",
    "painter": "Services", "plumber": "Services",
    "electrician": "Services",
    "lodging": "Travel & Accommodation",
    "travel_agency": "Travel & Accommodation",
    "hindu_temple": "Religious", "mosque": "Religious",
    "church": "Religious",
}


def get_api_key() -> str | None:
    """Get Google Maps API key from environment."""
    key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not key:
        print("❌ No API key found!")
        print("   Set environment variable: GOOGLE_MAPS_API_KEY=your_key")
        print("   Get free key: https://console.cloud.google.com/apis/credentials")
        print("   Enable 'Places API' in your Google Cloud project")
        return None
    return key


def nearby_search(api_key: str, lat: float, lng: float, place_type: str, radius: int = 5000) -> list[Any]:
    """
    Search for places near a location.
    Returns up to 20 results per call (can get up to 60 with next_page_token).
    """
    params = {
        "key": api_key,
        "location": f"{lat},{lng}",
        "radius": radius,
        "type": place_type,
        "language": "en",
    }
    
    all_results: list[Any] = []
    
    try:
        resp = requests.get(NEARBY_SEARCH_URL, params=params, timeout=15)
        data = resp.json()
        
        if data.get("status") == "OK":
            all_results.extend(data.get("results", []))
            
            # Get additional pages (up to 3 pages × 20 results = 60)
            next_token = data.get("next_page_token")
            page = 1
            while next_token and page < 3:
                time.sleep(2)  # Required delay for next_page_token
                params2 = {
                    "key": api_key,
                    "pagetoken": next_token,
                }
                resp2 = requests.get(NEARBY_SEARCH_URL, params=params2, timeout=15)
                data2 = resp2.json()
                if data2.get("status") == "OK":
                    all_results.extend(data2.get("results", []))
                    next_token = data2.get("next_page_token")
                    page += 1
                else:
                    break
        
        elif data.get("status") == "OVER_QUERY_LIMIT":
            print("    ⚠️  Query limit reached! Waiting 60 seconds...")
            time.sleep(60)
        
        elif data.get("status") == "REQUEST_DENIED":
            print(f"    ❌ Request denied: {data.get('error_message', 'Check API key')}")
    
    except Exception as e:
        print(f"    Error: {e}")
    
    return all_results


def text_search(api_key: str, query: str, location: tuple[float, float] | None = None) -> list[Any]:
    """
    Text-based place search.
    More flexible than Nearby Search — good for specific business types.
    """
    params: dict[str, str | int] = {
        "key": api_key,
        "query": query,
        "language": "en",
        "region": "in",  # India
    }
    
    if location:
        lat, lng = location
        params["location"] = f"{lat},{lng}"
        params["radius"] = 10000
    
    try:
        resp = requests.get(TEXT_SEARCH_URL, params=params, timeout=15)
        data = resp.json()
        
        if data.get("status") == "OK":
            return data.get("results", [])
        elif data.get("status") == "OVER_QUERY_LIMIT":
            print("    ⚠️  Query limit reached!")
            time.sleep(60)
    
    except Exception as e:
        print(f"    Error: {e}")
    
    return []


def extract_business_info(place: Any, city: str, place_type: str) -> dict[str, Any]:
    """Extract relevant business info from a Google Places result."""
    types = place.get("types", [])
    
    # Determine L1 category
    category = "Other"
    for t in types:
        if t in GOOGLE_TYPE_TO_L1:
            category = GOOGLE_TYPE_TO_L1[t]
            break
    
    return {
        "place_id": place.get("place_id", ""),
        "name": place.get("name", ""),
        "category": category,
        "subcategory": place_type.replace("_", " ").title(),
        "google_types": "|".join(types),
        "city": city,
        "address": place.get("vicinity", "") or place.get("formatted_address", ""),
        "lat": place.get("geometry", {}).get("location", {}).get("lat", ""),
        "lng": place.get("geometry", {}).get("location", {}).get("lng", ""),
        "rating": place.get("rating", ""),
        "user_ratings_total": place.get("user_ratings_total", ""),
        "price_level": place.get("price_level", ""),
        "source": "google_maps",
    }


def run_nearby_search_pipeline(api_key: str, cities: list[str] | None = None, types: list[str] | None = None, max_calls: int = 500) -> list[dict[str, Any]]:
    """Run Nearby Search for multiple cities and place types."""
    cities = cities or list(CITY_COORDS.keys())[:5]  # Default: top 5 cities
    types = types or PLACE_TYPES[:15]  # Default: first 15 types
    
    print(f"\n🗺️  Running Nearby Search:")
    print(f"   Cities: {len(cities)}")
    print(f"   Place types: {len(types)}")
    print(f"   Estimated API calls: {len(cities) * len(types)}")
    print(f"   Max calls limit: {max_calls}")
    
    all_businesses: list[dict[str, Any]] = []
    call_count = 0
    
    for city in cities:
        if city not in CITY_COORDS:
            print(f"  ⚠️  No coordinates for {city}, skipping")
            continue
        
        lat, lng = CITY_COORDS[city]
        
        for ptype in types:
            if call_count >= max_calls:
                print(f"\n  ⚠️  Reached max API calls ({max_calls})")
                return all_businesses
            
            print(f"  {city} / {ptype} (call #{call_count + 1})")
            results = nearby_search(api_key, lat, lng, ptype)
            
            for place in results:
                biz = extract_business_info(place, city, ptype)
                all_businesses.append(biz)
            
            call_count += 1
            time.sleep(0.5)  # Rate limit: ~2 requests/second
    
    print(f"\n  Total API calls: {call_count}")
    return all_businesses


def run_text_search_pipeline(api_key: str, max_calls: int = 200) -> list[dict[str, Any]]:
    """Run Text Search for specific Indian business queries."""
    queries = [
        # Chain restaurants
        "Dominos Pizza India", "Pizza Hut India", "McDonald's India",
        "Subway India", "KFC India", "Burger King India",
        "Starbucks India", "Cafe Coffee Day India",
        "Haldiram's India", "Bikanervala India",
        # Indian chains
        "Saravana Bhavan", "A2B Adyar Ananda Bhavan",
        "Sagar Ratna", "Naivedyam", "Udupi restaurants",
        # Retail chains
        "Reliance Fresh stores", "DMart stores India",
        "Big Bazaar India", "Spencer's Retail",
        "Croma electronics", "Vijay Sales",
        # Pharmacy chains
        "Apollo Pharmacy India", "MedPlus Pharmacy",
        "Netmeds pharmacy", "1mg pharmacy stores",
        # Fuel
        "Indian Oil petrol pump", "Hindustan Petroleum",
        "Bharat Petroleum pump",
        # Banking
        "State Bank of India branch", "HDFC Bank branch",
        "ICICI Bank branch", "Axis Bank branch",
        # Telecom
        "Jio store India", "Airtel store India",
        "Vi Vodafone store",
    ]
    
    print(f"\n🔍 Running Text Search for {len(queries)} queries...")
    
    all_businesses: list[dict[str, Any]] = []
    call_count = 0
    
    for query in queries:
        if call_count >= max_calls:
            break
        
        print(f"  Searching: {query}")
        results = text_search(api_key, query)
        
        for place in results:
            types = place.get("types", [])
            category = "Other"
            for t in types:
                if t in GOOGLE_TYPE_TO_L1:
                    category = GOOGLE_TYPE_TO_L1[t]
                    break
            
            all_businesses.append({
                "place_id": place.get("place_id", ""),
                "name": place.get("name", ""),
                "category": category,
                "subcategory": query.split()[0],
                "google_types": "|".join(types),
                "city": "",
                "address": place.get("formatted_address", ""),
                "lat": place.get("geometry", {}).get("location", {}).get("lat", ""),
                "lng": place.get("geometry", {}).get("location", {}).get("lng", ""),
                "rating": place.get("rating", ""),
                "user_ratings_total": place.get("user_ratings_total", ""),
                "price_level": place.get("price_level", ""),
                "source": "google_maps_text",
            })
        
        call_count += 1
        time.sleep(1)
    
    print(f"  Text search calls: {call_count}")
    return all_businesses


def save_results(businesses: list[dict[str, Any]], filename: str = "google_maps_businesses.csv") -> None:
    """Save results to CSV."""
    if not businesses:
        print("  No data to save")
        return
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filepath = OUTPUT_DIR / filename
    
    # Deduplicate by place_id
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for b in businesses:
        pid = b.get("place_id", "")
        if pid and pid not in seen:
            seen.add(pid)
            unique.append(b)
        elif not pid:
            unique.append(b)
    
    fieldnames: list[str] = list(unique[0].keys())
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unique)
    
    print(f"  Saved {len(unique):,} unique businesses to: {filepath}")
    
    # Print category distribution
    cats: defaultdict[str, int] = defaultdict(int)
    for b in unique:
        cats[b["category"]] += 1
    
    print("\n  Category distribution:")
    for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"    {cat:<30} {count:>6,}")


def main() -> None:
    print("=" * 60)
    print("GOOGLE MAPS PLACES API SCRAPER")
    print("=" * 60)
    
    api_key = get_api_key()
    if not api_key:
        print("\nTo use this script:")
        print("  1. Go to https://console.cloud.google.com/")
        print("  2. Create a project (or use existing)")
        print("  3. Enable 'Places API'")
        print("  4. Create API credentials")
        print("  5. Set env: $env:GOOGLE_MAPS_API_KEY='your_key'")
        print("\nFree tier: $200/month credit (~28,000 requests)")
        return
    
    print(f"\n✅ API key loaded")
    
    # Budget our free tier: 28,000 calls/month
    # Nearby Search: 500 calls max
    # Text Search: 200 calls max
    # Total: ~700 calls → well within free tier
    
    all_businesses: list[dict[str, Any]] = []
    
    # Phase 1: Nearby Search
    nearby = run_nearby_search_pipeline(api_key, max_calls=500)
    all_businesses.extend(nearby)
    
    # Phase 2: Text Search for known Indian chains
    text = run_text_search_pipeline(api_key, max_calls=200)
    all_businesses.extend(text)
    
    # Save
    save_results(all_businesses)
    
    # Also save raw JSON for reference
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    with open(RAW_DIR / "google_maps_raw.json", 'w', encoding='utf-8') as f:
        json.dump(all_businesses, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Done! Total businesses: {len(all_businesses):,}")


if __name__ == "__main__":
    main()
