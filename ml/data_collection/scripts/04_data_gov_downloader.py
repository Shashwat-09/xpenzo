"""
data.gov.in Dataset Downloader
Downloads relevant business/merchant datasets from India's Open Government Data Platform.

Dependencies: pip install requests pandas tqdm
API Key: Free registration at https://data.gov.in/user/register
Output: CSV files in raw/data_gov_in/

Available datasets (free, no API key needed for direct downloads):
  - MSME registered enterprises
  - FSSAI licensed food businesses  
  - GST registered businesses
  - Companies registered under MCA
"""

import os
import csv
import time
from typing import Any, TypeVar

import requests
from pathlib import Path

_T = TypeVar("_T")

try:
    from tqdm import tqdm  # type: ignore[import-untyped]
except ImportError:
    def tqdm(x: _T, **kw: Any) -> _T:
        return x

SCRIPT_DIR = Path(__file__).parent
RAW_DIR = SCRIPT_DIR.parent / "raw" / "data_gov_in"
OUTPUT_DIR = SCRIPT_DIR.parent / "processed"

# Known downloadable datasets from data.gov.in
# These are direct CSV/JSON download links (may need periodic updates)
DATASETS: dict[str, dict[str, str]] = {
    "msme_registered": {
        "name": "MSME Registered Enterprises",
        "description": "Micro, Small & Medium Enterprises registered with MSME Ministry",
        "url": "https://data.gov.in/catalog/micro-small-and-medium-enterprises",
        "api_url": "https://data.gov.in/resource/state-wise-no-micro-small-and-medium-enterprises-registered-udyam-platform",
        "category_mapping": "Business & Services",
    },
    "fssai_licensed": {
        "name": "FSSAI Licensed Food Businesses",
        "description": "Food businesses licensed by FSSAI",
        "url": "https://data.gov.in/catalog/fssai-license-registration-state-wise",
        "category_mapping": "Food & Dining",
    },
    "companies_mca": {
        "name": "MCA Registered Companies", 
        "description": "Companies registered under Ministry of Corporate Affairs",
        "url": "https://data.gov.in/catalog/companies-registered-during-each-year-under-companies-act-2013-and-earlier-acts",
        "category_mapping": "Business & Services",
    },
    "tourism_hotels": {
        "name": "Ministry of Tourism - Hotels",
        "description": "Classified hotels approved by Ministry of Tourism",
        "url": "https://data.gov.in/catalog/state-wise-number-classified-hotels-approved-ministry-tourism",
        "category_mapping": "Travel & Accommodation",
    },
    "education_institutions": {
        "name": "Educational Institutions",
        "description": "Schools, colleges, universities registered with AISHE",
        "url": "https://data.gov.in/catalog/all-india-survey-higher-education",
        "category_mapping": "Education",
    },
    "hospitals_directory": {
        "name": "Hospital Directory",
        "description": "Government and private hospitals",
        "url": "https://data.gov.in/catalog/hospital-directory",
        "category_mapping": "Healthcare",
    },
    "fuel_stations": {
        "name": "Fuel Retail Outlets",
        "description": "Petrol pumps and fuel stations across India",
        "url": "https://data.gov.in/catalog/petroleum-retail-outlets",
        "category_mapping": "Transportation",
    },
    "post_offices": {
        "name": "Post Office Network",
        "description": "India Post offices with pin codes",
        "url": "https://data.gov.in/catalog/all-india-pincode-directory",
        "category_mapping": "Services",
    },
    "banks_branches": {
        "name": "Bank Branch Directory",
        "description": "All bank branches (RBI master)",
        "url": "https://data.gov.in/catalog/list-all-bank-branches",
        "category_mapping": "Finance",
    },
}

# Alternative: data.gov.in API approach
# API documentation: https://data.gov.in/api-documentation
API_BASE = "https://api.data.gov.in/resource"

# Some known resource IDs with direct API access
DIRECT_API_RESOURCES: dict[str, dict[str, Any]] = {
    "pincode_directory": {
        "resource_id": "6176ee09-3d56-4a3b-8115-21841576b2f6",
        "fields": "officename,pincode,officeType,Deliverystatus,divisionname,regionname,circlename,Taluk,Districtname,statename",
        "limit": 1000,
    },
}


def download_with_api(
    resource_id: str,
    api_key: str | None = None,
    fields: str | None = None,
    limit: int = 1000,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Download data using data.gov.in API."""
    params: dict[str, str | int] = {
        "resource_id": resource_id,
        "format": "json",
        "limit": limit,
        "offset": offset,
    }
    if api_key:
        params["api-key"] = api_key
    if fields:
        params["fields"] = fields
    
    try:
        resp = requests.get(API_BASE, params=params, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("records", [])
        else:
            print(f"  API returned status {resp.status_code}")
            return []
    except Exception as e:
        print(f"  API error: {e}")
        return []


def download_pincode_directory(api_key: str | None = None) -> list[dict[str, Any]]:
    """Download India Pin Code directory — useful for mapping pincodes to cities/states."""
    print("\n📮 Downloading Pincode Directory...")
    
    resource: dict[str, Any] = DIRECT_API_RESOURCES["pincode_directory"]
    all_records: list[dict[str, Any]] = []
    offset: int = 0
    batch_size: int = 1000
    max_records: int = 200000  # Safety limit
    
    while offset < max_records:
        records = download_with_api(
            resource["resource_id"],
            api_key=api_key,
            fields=resource["fields"],
            limit=batch_size,
            offset=offset,
        )
        
        if not records:
            break
        
        all_records.extend(records)
        offset += batch_size
        
        if len(records) < batch_size:
            break
        
        print(f"  Downloaded {len(all_records):,} records...", end="\r")
        time.sleep(0.5)  # Rate limit
    
    print(f"  Total pincode records: {len(all_records):,}")
    
    if all_records:
        save_data(all_records, "pincode_directory.csv")
    
    return all_records


def scrape_data_gov_catalog() -> list[dict[str, str]]:
    """
    Scrape data.gov.in catalog pages for downloadable CSV links.
    Since direct API requires keys for many datasets, we can also
    try to find direct download links from catalog pages.
    """
    print("\n📊 Searching data.gov.in catalog for downloadable datasets...")
    
    found_links: list[dict[str, str]] = []
    
    search_terms = [
        "business+directory",
        "merchant+list",
        "shop+establishment",
        "restaurant+food",
        "hospital+directory",
        "school+directory",
        "hotel+tourism",
        "fuel+station",
        "bank+branch",
    ]
    
    for term in search_terms:
        print(f"  Searching: {term.replace('+', ' ')}")
        try:
            url = f"https://data.gov.in/catalog?search={term}&format=csv"
            resp = requests.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
            }, timeout=30)
            
            if resp.status_code == 200:
                from bs4 import BeautifulSoup  # type: ignore[import-untyped]
                soup: Any = BeautifulSoup(resp.text, 'lxml')
                
                for link in soup.find_all('a', href=True):
                    href: str = link['href']
                    if href.endswith('.csv') or 'download' in href.lower():
                        title: str = link.get_text(strip=True)
                        if title and len(title) > 5:
                            found_links.append({
                                "title": title,
                                "url": href if href.startswith('http') else f"https://data.gov.in{href}",
                                "search_term": term,
                            })
            
            time.sleep(2)
            
        except Exception as e:
            print(f"    Error: {e}")
    
    if found_links:
        print(f"\n  Found {len(found_links)} downloadable datasets:")
        for link in found_links[:20]:
            print(f"    • {link['title'][:80]}")
            print(f"      URL: {link['url']}")
    
    return found_links


def download_known_csvs() -> None:
    """
    Download well-known freely available CSVs from data.gov.in.
    These are manually curated direct download links.
    """
    print("\n📥 Downloading known datasets...")
    
    # Direct download URLs for commonly available datasets
    # These URLs may need updating if data.gov.in changes them
    direct_downloads: list[dict[str, str]] = [
        {
            "name": "All India Pincode Directory",
            "url": "https://data.gov.in/files/ogdpv2dms/s3fs-public/datafile/OGDCMS_Pincode_Dir.csv",
            "filename": "pincode_directory_direct.csv",
        },
    ]
    
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    for item in direct_downloads:
        filepath = RAW_DIR / item["filename"]
        if filepath.exists():
            print(f"  Already exists: {item['name']}")
            continue
        
        print(f"  Downloading: {item['name']}...")
        try:
            resp = requests.get(item["url"], stream=True, timeout=60)
            if resp.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                size_kb: float = filepath.stat().st_size / 1024
                print(f"    Saved: {filepath.name} ({size_kb:.0f} KB)")
            else:
                print(f"    HTTP {resp.status_code} — URL may have changed")
        except Exception as e:
            print(f"    Error: {e}")


def save_data(records: list[dict[str, Any]], filename: str) -> None:
    """Save records to CSV."""
    if not records:
        return
    
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    filepath = RAW_DIR / filename
    
    fieldnames: list[str] = list(records[0].keys())
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    
    print(f"  Saved {len(records):,} records to: {filepath}")


def main() -> None:
    print("=" * 60)
    print("DATA.GOV.IN DATASET DOWNLOADER")
    print("=" * 60)
    
    # Print available datasets
    print("\nAvailable datasets from data.gov.in:")
    for _key, info in DATASETS.items():
        print(f"  📁 {info['name']}")
        print(f"     Category: {info['category_mapping']}")
        print(f"     URL: {info['url']}")
    
    # Check for API key
    api_key = os.environ.get("DATA_GOV_IN_API_KEY")
    if api_key:
        print(f"\n✅ API key found in environment")
    else:
        print(f"\n⚠️  No API key found. Set DATA_GOV_IN_API_KEY env variable")
        print("   Get free key: https://data.gov.in/user/register")
        print("   Proceeding with direct downloads only...")
    
    # Step 1: Download known direct CSVs
    download_known_csvs()
    
    # Step 2: Try API-based downloads
    if api_key:
        download_pincode_directory(api_key)
    
    # Step 3: Catalog search for more links
    try:
        links = scrape_data_gov_catalog()
        if links:
            save_data(links, "catalog_links.csv")
    except ImportError:
        print("  BeautifulSoup not available, skipping catalog scrape")
    
    print("\n✅ Done!")
    print("\nManual downloads recommended (data.gov.in has authentication):")
    for _key, info in DATASETS.items():
        print(f"  • {info['name']}: {info['url']}")


if __name__ == "__main__":
    main()
