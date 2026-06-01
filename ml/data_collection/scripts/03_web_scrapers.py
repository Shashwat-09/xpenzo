"""
Web Scraper for Indian Business Directories
Scrapes business names and categories from:
  - Swiggy (restaurants)
  - Zomato (restaurants)  
  - Practo (healthcare)
  - JustDial (all businesses)
  - Sulekha (services)

Dependencies: pip install requests beautifulsoup4 lxml tqdm fake-useragent
Output: CSV files in processed/

IMPORTANT: Respect rate limits. Uses 2-5 second delays between requests.
           Set User-Agent to avoid blocks.
"""

import re
import csv
import json
import time
import random
import sys
from pathlib import Path
from typing import Any, cast

try:
    import requests
    from bs4 import BeautifulSoup  # type: ignore[import-untyped]
except ImportError:
    print("Install dependencies: pip install requests beautifulsoup4 lxml")
    sys.exit(1)

try:
    from tqdm import tqdm  # type: ignore[import-untyped]
except ImportError:
    def tqdm(x: Any, **kw: Any) -> Any:
        return x

# ────────────────────────────────────────────────────────
# CONFIG
# ────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
RAW_DIR = SCRIPT_DIR.parent / "raw"
OUTPUT_DIR = SCRIPT_DIR.parent / "processed"

# Major Indian cities to scrape
CITIES = [
    "mumbai", "delhi", "bangalore", "hyderabad", "chennai",
    "kolkata", "pune", "ahmedabad", "jaipur", "lucknow",
    "chandigarh", "indore", "bhopal", "nagpur", "visakhapatnam",
    "kochi", "coimbatore", "vadodara", "surat", "patna",
    "thiruvananthapuram", "guwahati", "bhubaneswar", "dehradun", "ranchi",
]

# Common headers to avoid bot detection
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

def polite_delay(min_sec: float = 2, max_sec: float = 5) -> None:
    """Random delay between requests to be polite."""
    time.sleep(random.uniform(min_sec, max_sec))


# ────────────────────────────────────────────────────────
# SWIGGY SCRAPER
# ────────────────────────────────────────────────────────
def scrape_swiggy_restaurants(cities: list[str] | None = None) -> list[dict[str, str]]:
    """
    Scrape restaurant names from Swiggy's city pages.
    Swiggy uses client-side rendering, so we target their API endpoints.
    """
    print("\n🍕 Scraping Swiggy restaurants...")
    cities = cities or CITIES[:10]  # Limit to top 10 cities
    restaurants: list[dict[str, str]] = []
    
    # Swiggy's internal API for restaurant listing
    # Note: These endpoints may change; update as needed
    _SWIGGY_API = "https://www.swiggy.com/dapi/restaurants/list/v5"
    
    for city in cities:
        print(f"  City: {city}")
        try:
            # Try the city restaurant page
            url = f"https://www.swiggy.com/city/{city}/best-restaurants"
            resp = requests.get(url, headers=HEADERS, timeout=30)
            
            if resp.status_code == 200:
                soup: Any = BeautifulSoup(resp.text, 'lxml')
                
                # Extract restaurant names from various possible selectors
                # Swiggy uses React, so look for JSON data in script tags
                for script in soup.find_all('script', type='application/ld+json'):
                    try:
                        data: Any = json.loads(str(script.string or ""))
                        if isinstance(data, dict):
                            d: dict[str, Any] = cast("dict[str, Any]", data)
                            if d.get("@type") == "Restaurant":
                                agg: Any = d.get("aggregateRating", {})
                                restaurants.append({
                                    "name": str(d.get("name", "")),
                                    "category": "Food & Dining",
                                    "subcategory": "Restaurant",
                                    "cuisine": str(d.get("servesCuisine", "")),
                                    "city": city,
                                    "source": "swiggy",
                                    "rating": str(agg.get("ratingValue", "")),
                                })
                        elif isinstance(data, list):
                            for raw_item in cast("list[Any]", data):
                                item: dict[str, Any] = cast("dict[str, Any]", raw_item)
                                if isinstance(raw_item, dict) and item.get("@type") == "Restaurant":
                                    agg2: Any = item.get("aggregateRating", {})
                                    restaurants.append({
                                        "name": str(item.get("name", "")),
                                        "category": "Food & Dining",
                                        "subcategory": "Restaurant",
                                        "cuisine": str(item.get("servesCuisine", "")),
                                        "city": city,
                                        "source": "swiggy",
                                        "rating": str(agg2.get("ratingValue", "")),
                                    })
                    except json.JSONDecodeError:
                        pass
                
                # Also try extracting from meta tags and visible text
                for tag in soup.find_all(['h2', 'h3', 'a'], class_=re.compile(r'RestaurantCard|restaurant', re.I)):
                    name = tag.get_text(strip=True)
                    if name and len(name) > 2 and len(name) < 100:
                        restaurants.append({
                            "name": name,
                            "category": "Food & Dining",
                            "subcategory": "Restaurant",
                            "cuisine": "",
                            "city": city,
                            "source": "swiggy",
                            "rating": "",
                        })
            
            polite_delay()
            
        except Exception as e:
            print(f"    Error scraping {city}: {e}")
            polite_delay(3, 8)
    
    # Deduplicate by name+city
    seen: set[tuple[str, str]] = set()
    unique: list[dict[str, str]] = []
    for r in restaurants:
        key = (r["name"].lower().strip(), r["city"])
        if key not in seen:
            seen.add(key)
            unique.append(r)
    
    print(f"  Total unique Swiggy restaurants: {len(unique):,}")
    return unique


# ────────────────────────────────────────────────────────
# ZOMATO SCRAPER
# ────────────────────────────────────────────────────────
def scrape_zomato_restaurants(cities: list[str] | None = None) -> list[dict[str, str]]:
    """Scrape restaurant data from Zomato city pages."""
    print("\n🍽️ Scraping Zomato restaurants...")
    cities = cities or CITIES[:10]
    restaurants: list[dict[str, str]] = []
    
    for city in cities:
        print(f"  City: {city}")
        try:
            url = f"https://www.zomato.com/{city}/best-restaurants"
            resp = requests.get(url, headers=HEADERS, timeout=30)
            
            if resp.status_code == 200:
                soup: Any = BeautifulSoup(resp.text, 'lxml')
                
                # Look for structured data
                for script in soup.find_all('script', type='application/ld+json'):
                    try:
                        data: Any = json.loads(str(script.string or ""))
                        items_list: list[Any] = cast("list[Any]", data if isinstance(data, list) else [data])
                        for raw_item in items_list:
                            item: dict[str, Any] = cast("dict[str, Any]", raw_item)
                            if isinstance(raw_item, dict) and item.get("@type") in ("Restaurant", "FoodEstablishment"):
                                agg: Any = item.get("aggregateRating", {})
                                addr_raw: Any = item.get("address", {})
                                addr: str = str(addr_raw.get("streetAddress", ""))
                                restaurants.append({
                                    "name": str(item.get("name", "")),
                                    "category": "Food & Dining",
                                    "subcategory": str(item.get("@type", "Restaurant")),
                                    "cuisine": str(item.get("servesCuisine", "")),
                                    "city": city,
                                    "source": "zomato",
                                    "rating": str(agg.get("ratingValue", "")),
                                    "address": addr,
                                })
                    except json.JSONDecodeError:
                        pass
                
                # Extract from page elements
                for card in soup.find_all('a', href=re.compile(r'/[a-z-]+/order')):
                    name = card.get_text(strip=True)
                    if name and 3 < len(name) < 80:
                        restaurants.append({
                            "name": name,
                            "category": "Food & Dining",
                            "subcategory": "Restaurant",
                            "cuisine": "",
                            "city": city,
                            "source": "zomato",
                            "rating": "",
                            "address": "",
                        })
            
            polite_delay()
            
        except Exception as e:
            print(f"    Error: {e}")
            polite_delay(3, 8)
    
    # Deduplicate
    seen: set[tuple[str, str]] = set()
    unique: list[dict[str, str]] = []
    for r in restaurants:
        key = (r["name"].lower().strip(), r["city"])
        if key not in seen:
            seen.add(key)
            unique.append(r)
    
    print(f"  Total unique Zomato restaurants: {len(unique):,}")
    return unique


# ────────────────────────────────────────────────────────
# PRACTO SCRAPER
# ────────────────────────────────────────────────────────
def scrape_practo_healthcare(cities: list[str] | None = None) -> list[dict[str, str]]:
    """Scrape healthcare provider names from Practo."""
    print("\n🏥 Scraping Practo healthcare providers...")
    cities = cities or CITIES[:10]
    providers: list[dict[str, str]] = []
    
    # Healthcare specialties to search
    specialties = [
        "general-physician", "dentist", "dermatologist", "gynecologist",
        "pediatrician", "orthopedist", "ophthalmologist", "cardiologist",
        "ent-specialist", "urologist", "psychiatrist", "physiotherapist",
    ]
    
    for city in cities:
        for specialty in specialties[:5]:  # Limit specialties per city
            print(f"  {city} / {specialty}")
            try:
                url = f"https://www.practo.com/{city}/{specialty}"
                resp = requests.get(url, headers=HEADERS, timeout=30)
                
                if resp.status_code == 200:
                    soup: Any = BeautifulSoup(resp.text, 'lxml')
                    
                    # Structured data
                    for script in soup.find_all('script', type='application/ld+json'):
                        try:
                            data: Any = json.loads(str(script.string or ""))
                            items_list: list[Any] = cast("list[Any]", data if isinstance(data, list) else [data])
                            for raw_item in items_list:
                                item: dict[str, Any] = cast("dict[str, Any]", raw_item)
                                if isinstance(raw_item, dict) and item.get("@type") in ("Physician", "MedicalBusiness", "Hospital"):
                                    agg_raw: Any = item.get("aggregateRating", {})
                                    rating: str = str(agg_raw.get("ratingValue", ""))
                                    providers.append({
                                        "name": str(item.get("name", "")),
                                        "category": "Healthcare",
                                        "subcategory": specialty.replace("-", " ").title(),
                                        "city": city,
                                        "source": "practo",
                                        "rating": rating,
                                    })
                        except json.JSONDecodeError:
                            pass
                    
                    # Extract from doctor cards
                    for card in soup.find_all(['h2', 'a'], attrs={"data-qa-id": re.compile(r'doctor_name', re.I)}):
                        name = card.get_text(strip=True)
                        if name and len(name) > 3:
                            providers.append({
                                "name": name,
                                "category": "Healthcare",
                                "subcategory": specialty.replace("-", " ").title(),
                                "city": city,
                                "source": "practo",
                                "rating": "",
                            })
                
                polite_delay()
                
            except Exception as e:
                print(f"    Error: {e}")
                polite_delay(3, 8)
    
    # Deduplicate
    seen: set[tuple[str, str]] = set()
    unique: list[dict[str, str]] = []
    for p in providers:
        key = (p["name"].lower().strip(), p["city"])
        if key not in seen:
            seen.add(key)
            unique.append(p)
    
    print(f"  Total unique Practo providers: {len(unique):,}")
    return unique


# ────────────────────────────────────────────────────────
# JUSTDIAL SCRAPER
# ────────────────────────────────────────────────────────
def scrape_justdial_businesses(cities: list[str] | None = None) -> list[dict[str, str]]:
    """Scrape business listings from JustDial."""
    print("\n📞 Scraping JustDial businesses...")
    cities = cities or CITIES[:10]
    businesses: list[dict[str, str]] = []
    
    # Business categories to search on JustDial
    categories = [
        "restaurants", "grocery-stores", "supermarkets",
        "beauty-parlours", "salons", "gyms",
        "electronics-shops", "mobile-phone-dealers",
        "hospitals", "clinics", "pharmacies",
        "petrol-pumps", "car-service-centres",
        "tailors", "laundry-services",
        "schools", "coaching-classes",
        "jewellers", "clothing-shops",
        "plumbers", "electricians", "carpenters",
        "caterers", "event-management",
        "travel-agents", "hotels",
    ]
    
    for city in cities:
        for cat in categories[:8]:  # Limit categories per city
            print(f"  {city} / {cat}")
            try:
                url = f"https://www.justdial.com/{city}/{cat}"
                session = requests.Session()
                session.max_redirects = 3
                resp = session.get(url, headers={
                    **HEADERS,
                    "Referer": "https://www.justdial.com/",
                }, timeout=15, allow_redirects=True)
                
                if resp.status_code == 200:
                    soup: Any = BeautifulSoup(resp.text, 'lxml')
                    
                    # JustDial structured data
                    for script in soup.find_all('script', type='application/ld+json'):
                        try:
                            data: Any = json.loads(str(script.string or ""))
                            items_list: list[Any] = cast("list[Any]", data if isinstance(data, list) else [data])
                            for raw_item in items_list:
                                item: dict[str, Any] = cast("dict[str, Any]", raw_item)
                                if isinstance(raw_item, dict) and item.get("name"):
                                    addr_raw: Any = item.get("address", {})
                                    addr: str = str(addr_raw.get("streetAddress", ""))
                                    businesses.append({
                                        "name": str(item.get("name", "")),
                                        "category": _jd_cat_to_l1(cat),
                                        "subcategory": cat.replace("-", " ").title(),
                                        "city": city,
                                        "source": "justdial",
                                        "address": addr,
                                        "phone": str(item.get("telephone", "")),
                                    })
                        except json.JSONDecodeError:
                            pass
                    
                    # Extract from listing cards
                    for card in soup.find_all(['span', 'a'], class_=re.compile(r'lng_cont_name|store-name', re.I)):
                        name = card.get_text(strip=True)
                        if name and 2 < len(name) < 100:
                            businesses.append({
                                "name": name,
                                "category": _jd_cat_to_l1(cat),
                                "subcategory": cat.replace("-", " ").title(),
                                "city": city,
                                "source": "justdial",
                                "address": "",
                                "phone": "",
                            })
                
                polite_delay()
                
            except KeyboardInterrupt:
                print(f"    Interrupted — saving what we have")
                break
            except Exception as e:
                print(f"    Error: {e}")
                polite_delay(3, 8)
        else:
            continue
        break  # Break outer loop if inner loop was broken
    
    # Deduplicate
    seen: set[tuple[str, str]] = set()
    unique: list[dict[str, str]] = []
    for b in businesses:
        key = (b["name"].lower().strip(), b["city"])
        if key not in seen:
            seen.add(key)
            unique.append(b)
    
    print(f"  Total unique JustDial businesses: {len(unique):,}")
    return unique


def _jd_cat_to_l1(jd_category: str) -> str:
    """Map JustDial category to our L1 category."""
    mapping: dict[str, str] = {
        "restaurants": "Food & Dining",
        "grocery-stores": "Shopping",
        "supermarkets": "Shopping",
        "beauty-parlours": "Services",
        "salons": "Services",
        "gyms": "Fitness & Wellness",
        "electronics-shops": "Shopping",
        "mobile-phone-dealers": "Shopping",
        "hospitals": "Healthcare",
        "clinics": "Healthcare",
        "pharmacies": "Healthcare",
        "petrol-pumps": "Transportation",
        "car-service-centres": "Transportation",
        "tailors": "Services",
        "laundry-services": "Services",
        "schools": "Education",
        "coaching-classes": "Education",
        "jewellers": "Shopping",
        "clothing-shops": "Shopping",
        "plumbers": "Services",
        "electricians": "Services",
        "carpenters": "Services",
        "caterers": "Food & Dining",
        "event-management": "Services",
        "travel-agents": "Travel & Accommodation",
        "hotels": "Travel & Accommodation",
    }
    return mapping.get(jd_category, "Other")


# ────────────────────────────────────────────────────────
# SULEKHA SCRAPER
# ────────────────────────────────────────────────────────
def scrape_sulekha_services(cities: list[str] | None = None) -> list[dict[str, str]]:
    """Scrape service provider names from Sulekha."""
    print("\n🔧 Scraping Sulekha services...")
    cities = cities or CITIES[:10]
    services: list[dict[str, str]] = []
    
    service_types = [
        "packers-and-movers", "pest-control", "home-cleaning",
        "interior-designers", "architects", "wedding-planners",
        "car-repair", "ac-repair", "water-purifier-repair",
        "tuition-teachers", "yoga-classes", "dance-classes",
    ]
    
    for city in cities:
        for svc in service_types[:5]:
            print(f"  {city} / {svc}")
            try:
                url = f"https://www.sulekha.com/{svc}/{city}"
                resp = requests.get(url, headers=HEADERS, timeout=30)
                
                if resp.status_code == 200:
                    soup: Any = BeautifulSoup(resp.text, 'lxml')
                    
                    for script in soup.find_all('script', type='application/ld+json'):
                        try:
                            data: Any = json.loads(str(script.string or ""))
                            items_list: list[Any] = cast("list[Any]", data if isinstance(data, list) else [data])
                            for raw_item in items_list:
                                item: dict[str, Any] = cast("dict[str, Any]", raw_item)
                                if isinstance(raw_item, dict) and item.get("name"):
                                    services.append({
                                        "name": str(item.get("name", "")),
                                        "category": "Services",
                                        "subcategory": svc.replace("-", " ").title(),
                                        "city": city,
                                        "source": "sulekha",
                                    })
                        except json.JSONDecodeError:
                            pass
                
                polite_delay()
                
            except Exception as e:
                print(f"    Error: {e}")
                polite_delay(3, 8)
    
    # Deduplicate
    seen: set[tuple[str, str]] = set()
    unique: list[dict[str, str]] = []
    for s in services:
        key = (s["name"].lower().strip(), s["city"])
        if key not in seen:
            seen.add(key)
            unique.append(s)
    
    print(f"  Total unique Sulekha services: {len(unique):,}")
    return unique


# ────────────────────────────────────────────────────────
# SAVE & MERGE
# ────────────────────────────────────────────────────────
def save_results(data: list[dict[str, str]], filename: str) -> None:
    """Save scraped data to CSV."""
    if not data:
        print(f"  No data for {filename}")
        return
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filepath = OUTPUT_DIR / filename
    
    fieldnames = list(data[0].keys())
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"  Saved {len(data):,} records to: {filepath}")


def main() -> None:
    """Run all scrapers and save results."""
    print("=" * 60)
    print("INDIAN BUSINESS DIRECTORY SCRAPER")
    print("=" * 60)
    print()
    print("⚠️  This script respects rate limits (2-5s between requests).")
    print("    Full scrape of all sources may take 2-4 hours.")
    print("    You can run individual scrapers by passing arguments:")
    print("    python 03_web_scrapers.py swiggy zomato practo justdial sulekha")
    print()
    
    # Parse command-line args for selective scraping
    targets = set(sys.argv[1:]) if len(sys.argv) > 1 else {"all"}
    run_all = "all" in targets
    
    all_businesses: list[dict[str, str]] = []
    
    if run_all or "swiggy" in targets:
        data = scrape_swiggy_restaurants()
        save_results(data, "scraped_swiggy.csv")
        all_businesses.extend(data)
    
    if run_all or "zomato" in targets:
        data = scrape_zomato_restaurants()
        save_results(data, "scraped_zomato.csv")
        all_businesses.extend(data)
    
    if run_all or "practo" in targets:
        data = scrape_practo_healthcare()
        save_results(data, "scraped_practo.csv")
        all_businesses.extend(data)
    
    if run_all or "justdial" in targets:
        data = scrape_justdial_businesses()
        save_results(data, "scraped_justdial.csv")
        all_businesses.extend(data)
    
    if run_all or "sulekha" in targets:
        data = scrape_sulekha_services()
        save_results(data, "scraped_sulekha.csv")
        all_businesses.extend(data)
    
    # Save merged results
    if all_businesses:
        save_results(all_businesses, "scraped_all_merged.csv")
    
    print(f"\n✅ Total scraped: {len(all_businesses):,} business listings")
    print("\nNext steps:")
    print("  1. Review CSV files for quality and deduplication")
    print("  2. Run labeling pipeline (Copilot Pro / Gemini)")
    print("  3. Merge with OSM and other data sources")


if __name__ == "__main__":
    main()
