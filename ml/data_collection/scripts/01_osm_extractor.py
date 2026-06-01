"""
OSM (OpenStreetMap) India Data Extractor
Downloads India OSM data and extracts business/POI names with categories.

Dependencies: pip install osmium pandas tqdm requests
Data source: https://download.geofabrik.de/asia/india-latest.osm.pbf (~1.5GB)
Output: CSV with columns [osm_id, name, category, subcategory, city, state, lat, lon]
"""

import sys
import csv
import requests
from pathlib import Path
from collections import defaultdict
from typing import Any

# Try importing optional deps, provide install instructions if missing
try:
    import osmium  # type: ignore[import-untyped]
except ImportError:
    print("Install osmium: pip install osmium")
    sys.exit(1)

try:
    from tqdm import tqdm  # type: ignore[import-untyped]
except ImportError:
    # Fallback: no progress bar
    def tqdm(x: Any, **kw: Any) -> Any:
        return x

# ────────────────────────────────────────────────────────
# CONFIG
# ────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
RAW_DIR = SCRIPT_DIR.parent / "raw" / "osm"
OUTPUT_DIR = SCRIPT_DIR.parent / "processed"
PBF_URL = "https://download.geofabrik.de/asia/india-latest.osm.pbf"
PBF_FILE = RAW_DIR / "india-latest.osm.pbf"
OUTPUT_CSV = OUTPUT_DIR / "osm_india_businesses.csv"

# OSM tags that indicate a business/merchant
BUSINESS_TAGS: dict[str, bool | set[str]] = {
    "shop": True,           # All shop types
    "amenity": {
        "restaurant", "cafe", "fast_food", "bar", "pub", "food_court",
        "pharmacy", "hospital", "clinic", "dentist", "doctors", "veterinary",
        "bank", "atm", "bureau_de_change",
        "fuel", "car_wash", "car_rental", "parking",
        "cinema", "theatre", "nightclub",
        "school", "college", "university", "kindergarten",
        "gym", "fitness_centre",
        "place_of_worship", "marketplace",
        "post_office", "library", "community_centre",
    },
    "tourism": {
        "hotel", "motel", "guest_house", "hostel", "camp_site",
        "museum", "gallery", "zoo", "theme_park", "aquarium",
    },
    "leisure": {
        "sports_centre", "swimming_pool", "fitness_centre", "stadium",
        "park", "garden", "playground", "water_park",
    },
    "office": True,         # All office types
    "craft": True,          # All craft types
    "healthcare": True,     # All healthcare types
}

# Map OSM tags to our L1 categories
TAG_TO_CATEGORY: dict[str, tuple[str, str]] = {
    # Food & Dining
    "restaurant": ("Food & Dining", "Restaurant"),
    "cafe": ("Food & Dining", "Cafe"),
    "fast_food": ("Food & Dining", "Fast Food"),
    "bar": ("Food & Dining", "Bar"),
    "pub": ("Food & Dining", "Bar"),
    "food_court": ("Food & Dining", "Food Court"),
    "bakery": ("Food & Dining", "Bakery"),
    "ice_cream": ("Food & Dining", "Desserts"),
    
    # Shopping
    "supermarket": ("Shopping", "Supermarket"),
    "convenience": ("Shopping", "Convenience Store"),
    "clothes": ("Shopping", "Clothing"),
    "electronics": ("Shopping", "Electronics"),
    "mobile_phone": ("Shopping", "Mobile & Accessories"),
    "jewelry": ("Shopping", "Jewellery"),
    "shoes": ("Shopping", "Footwear"),
    "books": ("Shopping", "Books & Stationery"),
    "stationery": ("Shopping", "Books & Stationery"),
    "hardware": ("Shopping", "Hardware"),
    "furniture": ("Shopping", "Furniture"),
    "department_store": ("Shopping", "Department Store"),
    "mall": ("Shopping", "Mall"),
    "optician": ("Shopping", "Eyewear"),
    "cosmetics": ("Shopping", "Beauty & Cosmetics"),
    "variety_store": ("Shopping", "General Store"),
    "general": ("Shopping", "General Store"),
    "greengrocer": ("Shopping", "Grocery"),
    "butcher": ("Shopping", "Meat & Poultry"),
    "seafood": ("Shopping", "Fish & Seafood"),
    "florist": ("Shopping", "Florist"),
    "gift": ("Shopping", "Gifts"),
    "sports": ("Shopping", "Sports Equipment"),
    "toys": ("Shopping", "Toys"),
    "pet": ("Shopping", "Pet Supplies"),
    
    # Healthcare
    "pharmacy": ("Healthcare", "Pharmacy"),
    "hospital": ("Healthcare", "Hospital"),
    "clinic": ("Healthcare", "Clinic"),
    "dentist": ("Healthcare", "Dentist"),
    "doctors": ("Healthcare", "Doctor"),
    "veterinary": ("Healthcare", "Veterinary"),
    
    # Transportation
    "fuel": ("Transportation", "Fuel Station"),
    "car_wash": ("Transportation", "Car Wash"),
    "car_rental": ("Transportation", "Car Rental"),
    "parking": ("Transportation", "Parking"),
    "car_repair": ("Transportation", "Car Service"),
    "car": ("Transportation", "Car Dealer"),
    "motorcycle": ("Transportation", "Two-Wheeler Dealer"),
    "bicycle": ("Transportation", "Bicycle Shop"),
    
    # Finance
    "bank": ("Finance", "Bank"),
    "atm": ("Finance", "ATM"),
    "bureau_de_change": ("Finance", "Currency Exchange"),
    
    # Entertainment
    "cinema": ("Entertainment", "Cinema"),
    "theatre": ("Entertainment", "Theatre"),
    "nightclub": ("Entertainment", "Nightclub"),
    "museum": ("Entertainment", "Museum"),
    "gallery": ("Entertainment", "Art Gallery"),
    "zoo": ("Entertainment", "Zoo"),
    "theme_park": ("Entertainment", "Theme Park"),
    "aquarium": ("Entertainment", "Aquarium"),
    
    # Education
    "school": ("Education", "School"),
    "college": ("Education", "College"),
    "university": ("Education", "University"),
    "kindergarten": ("Education", "Pre-School"),
    
    # Fitness & Wellness
    "gym": ("Fitness & Wellness", "Gym"),
    "fitness_centre": ("Fitness & Wellness", "Gym"),
    "sports_centre": ("Fitness & Wellness", "Sports Complex"),
    "swimming_pool": ("Fitness & Wellness", "Swimming Pool"),
    
    # Travel & Accommodation
    "hotel": ("Travel & Accommodation", "Hotel"),
    "motel": ("Travel & Accommodation", "Motel"),
    "guest_house": ("Travel & Accommodation", "Guest House"),
    "hostel": ("Travel & Accommodation", "Hostel"),
    "camp_site": ("Travel & Accommodation", "Camping"),
    
    # Services
    "hairdresser": ("Services", "Salon"),
    "beauty": ("Services", "Beauty Parlour"),
    "laundry": ("Services", "Laundry"),
    "dry_cleaning": ("Services", "Dry Cleaning"),
    "tailor": ("Services", "Tailor"),
    "copyshop": ("Services", "Printing"),
    "computer": ("Services", "Computer Repair"),
    "locksmith": ("Services", "Locksmith"),
    "post_office": ("Services", "Post Office"),
    
    # Religious
    "place_of_worship": ("Religious", "Temple/Mosque/Church"),
}


class BusinessHandler(osmium.SimpleHandler):  # type: ignore[misc]
    """OSM handler that extracts business/POI nodes and ways."""
    
    def __init__(self) -> None:
        super().__init__()  # type: ignore[reportUnknownMemberType]
        self.businesses: list[dict[str, str]] = []
        self.count: int = 0
        
    def _extract_business(self, tags: Any, lat: float | None = None, lon: float | None = None, osm_id: int | None = None, osm_type: str = "node") -> None:
        """Extract business info from OSM tags."""
        name: str | None = tags.get("name") or tags.get("name:en") or tags.get("brand")
        if not name:
            return  # Skip unnamed entities
        
        # Determine category from tags
        category: str | None = None
        subcategory: str | None = None
        tag_value: str = ""
        
        for tag_key in ["shop", "amenity", "tourism", "leisure", "office", "craft", "healthcare"]:
            if tag_key in tags:
                tag_value = str(tags[tag_key])
                if tag_value in TAG_TO_CATEGORY:
                    category, subcategory = TAG_TO_CATEGORY[tag_value]
                elif tag_key == "shop":
                    category, subcategory = "Shopping", tag_value.replace("_", " ").title()
                elif tag_key == "office":
                    category, subcategory = "Business & Office", tag_value.replace("_", " ").title()
                elif tag_key == "craft":
                    category, subcategory = "Services", tag_value.replace("_", " ").title()
                elif tag_key == "healthcare":
                    category, subcategory = "Healthcare", tag_value.replace("_", " ").title()
                break
        
        if not category or not subcategory:
            return
        
        # Extract additional metadata
        city: str = tags.get("addr:city", "") or ""
        state: str = tags.get("addr:state", "") or ""
        brand: str = tags.get("brand", "") or ""
        cuisine: str = tags.get("cuisine", "") or ""
        phone: str = tags.get("phone", "") or tags.get("contact:phone", "") or ""
        website: str = tags.get("website", "") or tags.get("contact:website", "") or ""
        
        self.businesses.append({
            "osm_id": f"{osm_type}/{osm_id}",
            "name": name,
            "brand": brand,
            "category": category,
            "subcategory": subcategory,
            "osm_tag": f"{tag_value}" if tag_value else "",
            "cuisine": cuisine,
            "city": city,
            "state": state,
            "lat": f"{lat:.6f}" if lat else "",
            "lon": f"{lon:.6f}" if lon else "",
            "phone": phone,
            "website": website,
        })
        self.count += 1
        
        if self.count % 50000 == 0:
            print(f"  Extracted {self.count:,} businesses...")
    
    def node(self, n: Any) -> None:
        """Process OSM nodes."""
        self._extract_business(
            n.tags, 
            lat=n.location.lat if n.location.valid() else None,
            lon=n.location.lon if n.location.valid() else None,
            osm_id=n.id,
            osm_type="node"
        )
    
    def way(self, w: Any) -> None:
        """Process OSM ways (buildings, areas)."""
        self._extract_business(
            w.tags,
            osm_id=w.id,
            osm_type="way"
        )


def download_pbf() -> bool:
    """Download India OSM PBF file (~1.5 GB)."""
    if PBF_FILE.exists():
        size_mb = PBF_FILE.stat().st_size / (1024 * 1024)
        print(f"PBF file already exists ({size_mb:.0f} MB): {PBF_FILE}")
        if size_mb > 100:  # At least 100MB means it's probably complete
            return True
    
    print(f"Downloading India OSM data from Geofabrik...")
    print(f"URL: {PBF_URL}")
    print(f"This is ~1.5 GB, may take 10-30 minutes depending on connection.")
    
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        response = requests.get(PBF_URL, stream=True)
        response.raise_for_status()
        total = int(response.headers.get('content-length', 0))
        
        with open(PBF_FILE, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192 * 16):
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    pct = (downloaded / total) * 100
                    mb_done = downloaded / (1024 * 1024)
                    mb_total = total / (1024 * 1024)
                    print(f"\r  Progress: {pct:.1f}% ({mb_done:.0f}/{mb_total:.0f} MB)", end="", flush=True)
        print()
        return True
    except Exception as e:
        print(f"Download failed: {e}")
        print("You can manually download from:")
        print(f"  {PBF_URL}")
        print(f"  Save to: {PBF_FILE}")
        return False


def extract_businesses() -> list[dict[str, str]]:
    """Extract business data from OSM PBF file."""
    print(f"Extracting businesses from: {PBF_FILE}")
    print("This may take 5-15 minutes for the full India dataset...")
    
    handler = BusinessHandler()
    handler.apply_file(str(PBF_FILE), locations=True)  # type: ignore[reportUnknownMemberType]
    
    print(f"\nTotal businesses extracted: {handler.count:,}")
    return handler.businesses


def save_to_csv(businesses: list[dict[str, str]]) -> None:
    """Save extracted businesses to CSV."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    fieldnames: list[str] = [
        "osm_id", "name", "brand", "category", "subcategory", 
        "osm_tag", "cuisine", "city", "state", "lat", "lon", 
        "phone", "website"
    ]
    
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(businesses)
    
    print(f"Saved {len(businesses):,} businesses to: {OUTPUT_CSV}")


def print_stats(businesses: list[dict[str, str]]) -> None:
    """Print category distribution statistics."""
    cat_counts: defaultdict[str, int] = defaultdict(int)
    subcat_counts: defaultdict[str, int] = defaultdict(int)
    brand_counts: defaultdict[str, int] = defaultdict(int)
    
    for b in businesses:
        cat_counts[b["category"]] += 1
        subcat_counts[f"{b['category']} > {b['subcategory']}"] += 1
        if b["brand"]:
            brand_counts[b["brand"]] += 1
    
    print("\n" + "="*60)
    print("CATEGORY DISTRIBUTION")
    print("="*60)
    for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat:<30} {count:>8,}")
    
    print(f"\n  Total categories: {len(cat_counts)}")
    print(f"  Total subcategories: {len(subcat_counts)}")
    print(f"  Unique brands: {len(brand_counts)}")
    
    print("\n  Top 20 brands:")
    for brand, count in sorted(brand_counts.items(), key=lambda x: -x[1])[:20]:
        print(f"    {brand:<40} {count:>6,}")


def main() -> None:
    print("="*60)
    print("OSM INDIA BUSINESS EXTRACTOR")
    print("="*60)
    
    # Step 1: Download
    if not download_pbf():
        sys.exit(1)
    
    # Step 2: Extract
    businesses = extract_businesses()
    
    if not businesses:
        print("No businesses found. Check if PBF file is valid.")
        sys.exit(1)
    
    # Step 3: Save
    save_to_csv(businesses)
    
    # Step 4: Stats
    print_stats(businesses)
    
    print("\n✅ Done! Next steps:")
    print("  1. Review the CSV for quality")
    print("  2. Run the labeling pipeline to assign L1/L2/L3 categories")
    print("  3. Merge with other data sources")


if __name__ == "__main__":
    main()
