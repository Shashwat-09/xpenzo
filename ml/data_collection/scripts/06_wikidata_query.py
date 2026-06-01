"""
Wikidata SPARQL Query Script for Indian Businesses
Fetches structured business data from Wikidata — India's companies, brands, 
restaurant chains, retail stores, hospital chains, etc.

Wikidata is 100% free, no API key needed.
SPARQL endpoint: https://query.wikidata.org/sparql

Dependencies: pip install requests pandas tqdm
Output: processed/wikidata_businesses.csv
"""

from __future__ import annotations

import csv
import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import requests

SCRIPT_DIR = Path(__file__).parent
RAW_DIR = SCRIPT_DIR.parent / "raw" / "wikidata"
OUTPUT_DIR = SCRIPT_DIR.parent / "processed"

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"

# User-Agent required by Wikidata query service
HEADERS = {
    "User-Agent": "XpenzoMLDataCollector/1.0 (expense-tracker-research; Python/requests)",
    "Accept": "application/sparql-results+json",
}


# ────────────────────────────────────────────────────────────
# SPARQL Queries — each targets a specific business category
# ────────────────────────────────────────────────────────────

QUERIES: dict[str, str] = {
    # 1. Indian companies (broad — P17=India, P31=company/business)
    "indian_companies": """
        SELECT DISTINCT ?item ?itemLabel ?itemDescription ?industryLabel ?hqLabel ?inceptionYear WHERE {
          ?item wdt:P17 wd:Q668 .        # country: India
          ?item wdt:P31/wdt:P279* wd:Q4830453 .  # instance of: business enterprise (or subclass)
          OPTIONAL { ?item wdt:P452 ?industry . }
          OPTIONAL { ?item wdt:P159 ?hq . }
          OPTIONAL { ?item wdt:P571 ?inception . BIND(YEAR(?inception) AS ?inceptionYear) }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en,hi" . }
        }
        LIMIT 5000
    """,

    # 2. Restaurant chains operating in India
    "restaurant_chains": """
        SELECT DISTINCT ?item ?itemLabel ?itemDescription ?countryLabel ?cuisineLabel WHERE {
          {
            ?item wdt:P31/wdt:P279* wd:Q4191791 .  # restaurant chain
            ?item wdt:P17 wd:Q668 .                  # country: India
          } UNION {
            ?item wdt:P31/wdt:P279* wd:Q4191791 .  # restaurant chain
            ?item wdt:P159 ?hq .
            ?hq wdt:P17 wd:Q668 .                  # HQ in India
          } UNION {
            ?item wdt:P31/wdt:P279* wd:Q4191791 .
            ?item wdt:P2541 wd:Q668 .               # operating area: India
          }
          OPTIONAL { ?item wdt:P2012 ?cuisine . }
          OPTIONAL { ?item wdt:P17 ?country . }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en,hi" . }
        }
        LIMIT 2000
    """,

    # 3. Fast food / QSR chains in India
    "fast_food_india": """
        SELECT DISTINCT ?item ?itemLabel ?itemDescription WHERE {
          ?item wdt:P31/wdt:P279* wd:Q1002697 .  # fast food restaurant chain
          {
            ?item wdt:P17 wd:Q668 .
          } UNION {
            ?item wdt:P2541 wd:Q668 .
          }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en,hi" . }
        }
        LIMIT 500
    """,

    # 4. Retail chains / stores
    "retail_chains": """
        SELECT DISTINCT ?item ?itemLabel ?itemDescription ?industryLabel WHERE {
          {
            ?item wdt:P31/wdt:P279* wd:Q507619 .  # retail store chain
            ?item wdt:P17 wd:Q668 .
          } UNION {
            ?item wdt:P31/wdt:P279* wd:Q507619 .
            ?item wdt:P2541 wd:Q668 .
          }
          OPTIONAL { ?item wdt:P452 ?industry . }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en,hi" . }
        }
        LIMIT 2000
    """,

    # 5. Indian banks
    "indian_banks": """
        SELECT DISTINCT ?item ?itemLabel ?itemDescription ?typeLabel ?swiftCode WHERE {
          ?item wdt:P17 wd:Q668 .
          ?item wdt:P31/wdt:P279* wd:Q22687 .  # bank
          OPTIONAL { ?item wdt:P31 ?type . }
          OPTIONAL { ?item wdt:P2627 ?swiftCode . }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en,hi" . }
        }
        LIMIT 1000
    """,

    # 6. Hospital chains / medical facilities
    "hospitals_india": """
        SELECT DISTINCT ?item ?itemLabel ?itemDescription ?cityLabel ?bedCount WHERE {
          ?item wdt:P17 wd:Q668 .
          {
            ?item wdt:P31/wdt:P279* wd:Q16917 .   # hospital
          } UNION {
            ?item wdt:P31/wdt:P279* wd:Q4260475 .  # hospital chain
          }
          OPTIONAL { ?item wdt:P131 ?city . }
          OPTIONAL { ?item wdt:P6801 ?bedCount . }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en,hi" . }
        }
        LIMIT 2000
    """,

    # 7. Indian universities & colleges
    "education_india": """
        SELECT DISTINCT ?item ?itemLabel ?itemDescription ?cityLabel ?typeLabel WHERE {
          ?item wdt:P17 wd:Q668 .
          {
            ?item wdt:P31/wdt:P279* wd:Q3918 .   # university
          } UNION {
            ?item wdt:P31/wdt:P279* wd:Q189004 .  # college
          }
          OPTIONAL { ?item wdt:P131 ?city . }
          OPTIONAL { ?item wdt:P31 ?type . }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en,hi" . }
        }
        LIMIT 3000
    """,

    # 8. Indian brands (consumer brands headquartered in India)
    "indian_brands": """
        SELECT DISTINCT ?item ?itemLabel ?itemDescription ?ownerLabel ?industryLabel WHERE {
          ?item wdt:P17 wd:Q668 .
          ?item wdt:P31/wdt:P279* wd:Q431289 .  # brand
          OPTIONAL { ?item wdt:P127 ?owner . }
          OPTIONAL { ?item wdt:P452 ?industry . }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en,hi" . }
        }
        LIMIT 3000
    """,

    # 9. Indian telecom operators
    "telecom_india": """
        SELECT DISTINCT ?item ?itemLabel ?itemDescription ?parentLabel WHERE {
          ?item wdt:P17 wd:Q668 .
          ?item wdt:P31/wdt:P279* wd:Q2401749 .  # telecom company
          OPTIONAL { ?item wdt:P749 ?parent . }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en,hi" . }
        }
        LIMIT 500
    """,

    # 10. Indian insurers
    "insurance_india": """
        SELECT DISTINCT ?item ?itemLabel ?itemDescription ?typeLabel WHERE {
          ?item wdt:P17 wd:Q668 .
          ?item wdt:P31/wdt:P279* wd:Q6023980 .  # insurance company
          OPTIONAL { ?item wdt:P31 ?type . }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en,hi" . }
        }
        LIMIT 500
    """,

    # 11. Hotels and hotel chains in India
    "hotels_india": """
        SELECT DISTINCT ?item ?itemLabel ?itemDescription ?cityLabel ?starsLabel WHERE {
          ?item wdt:P17 wd:Q668 .
          {
            ?item wdt:P31/wdt:P279* wd:Q27686 .   # hotel
          } UNION {
            ?item wdt:P31/wdt:P279* wd:Q2178147 .  # hotel chain
          }
          OPTIONAL { ?item wdt:P131 ?city . }
          OPTIONAL { ?item wdt:P2439 ?stars . }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en,hi" . }
        }
        LIMIT 2000
    """,

    # 12. E-commerce platforms in India
    "ecommerce_india": """
        SELECT DISTINCT ?item ?itemLabel ?itemDescription ?foundedLabel WHERE {
          {
            ?item wdt:P31/wdt:P279* wd:Q484847 .   # e-commerce
            ?item wdt:P17 wd:Q668 .
          } UNION {
            ?item wdt:P31/wdt:P279* wd:Q3561954 .  # online marketplace
            ?item wdt:P17 wd:Q668 .
          }
          OPTIONAL { ?item wdt:P571 ?founded . }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en,hi" . }
        }
        LIMIT 500
    """,

    # 13. Transport companies (airlines, railways, ride-hailing)
    "transport_india": """
        SELECT DISTINCT ?item ?itemLabel ?itemDescription ?typeLabel WHERE {
          ?item wdt:P17 wd:Q668 .
          {
            ?item wdt:P31/wdt:P279* wd:Q46970 .   # airline
          } UNION {
            ?item wdt:P31/wdt:P279* wd:Q728937 .  # rail operator
          } UNION {
            ?item wdt:P31/wdt:P279* wd:Q190117 .  # bus company
          }
          OPTIONAL { ?item wdt:P31 ?type . }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en,hi" . }
        }
        LIMIT 500
    """,

    # 14. Indian cinema chains / multiplexes
    "cinema_india": """
        SELECT DISTINCT ?item ?itemLabel ?itemDescription WHERE {
          ?item wdt:P17 wd:Q668 .
          {
            ?item wdt:P31/wdt:P279* wd:Q41253 .  # movie theater
          } UNION {
            ?item wdt:P31/wdt:P279* wd:Q9752640 . # cinema chain
          }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en,hi" . }
        }
        LIMIT 500
    """,
}

# Map query categories to our L1 classification
QUERY_TO_L1: dict[str, str] = {
    "indian_companies": "Business",
    "restaurant_chains": "Food & Dining",
    "fast_food_india": "Food & Dining",
    "retail_chains": "Shopping",
    "indian_banks": "Finance",
    "hospitals_india": "Healthcare",
    "education_india": "Education",
    "indian_brands": "Shopping",
    "telecom_india": "Telecom",
    "insurance_india": "Finance",
    "hotels_india": "Travel & Accommodation",
    "ecommerce_india": "Shopping",
    "transport_india": "Transportation",
    "cinema_india": "Entertainment",
}


def run_sparql_query(query_name: str, sparql: str) -> list[dict[str, Any]]:
    """Execute a SPARQL query against Wikidata."""
    print(f"\n  🔍 Running: {query_name}")
    
    params: dict[str, str] = {
        "query": sparql.strip(),
        "format": "json",
    }
    
    try:
        resp = requests.get(
            SPARQL_ENDPOINT,
            params=params,
            headers=HEADERS,
            timeout=120,
        )
        
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", {}).get("bindings", [])
            print(f"     ✅ Got {len(results):,} results")
            return results
        elif resp.status_code == 429:
            print(f"     ⚠️  Rate limited. Waiting 30s...")
            time.sleep(30)
            return run_sparql_query(query_name, sparql)  # Retry once
        else:
            print(f"     ❌ HTTP {resp.status_code}: {resp.text[:200]}")
            return []
    
    except requests.exceptions.Timeout:
        print(f"     ⏱️  Query timed out (120s). Wikidata may be busy.")
        return []
    except Exception as e:
        print(f"     ❌ Error: {e}")
        return []


def extract_value(binding: dict[str, Any], field: str) -> str:
    """Extract value from SPARQL result binding."""
    if field in binding:
        return binding[field].get("value", "")
    return ""


def process_results(query_name: str, results: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Convert SPARQL results to flat records."""
    records: list[dict[str, str]] = []
    l1_category: str = QUERY_TO_L1.get(query_name, "Other")
    
    for r in results:
        wikidata_id = extract_value(r, "item").split("/")[-1] if "item" in r else ""
        label = extract_value(r, "itemLabel")
        
        # Skip entries that are just QIDs (unlabeled)
        if label.startswith("Q") and label[1:].isdigit():
            continue
        
        record = {
            "wikidata_id": wikidata_id,
            "name": label,
            "description": extract_value(r, "itemDescription"),
            "category": l1_category,
            "subcategory": query_name.replace("_india", "").replace("indian_", "").replace("_", " ").title(),
            "industry": extract_value(r, "industryLabel"),
            "city": extract_value(r, "cityLabel") or extract_value(r, "hqLabel"),
            "source_query": query_name,
            "source": "wikidata",
        }
        
        # Additional fields per query type
        if "swiftCode" in r:
            record["swift_code"] = extract_value(r, "swiftCode")
        if "inceptionYear" in r:
            record["founded"] = extract_value(r, "inceptionYear")
        if "ownerLabel" in r:
            record["owner"] = extract_value(r, "ownerLabel")
        if "parentLabel" in r:
            record["parent_company"] = extract_value(r, "parentLabel")
        
        records.append(record)
    
    return records


def save_all(all_records: list[dict[str, str]]) -> None:
    """Save all records to CSV and JSON."""
    if not all_records:
        print("No records to save")
        return
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    # Deduplicate by wikidata_id
    seen: set[str] = set()
    unique: list[dict[str, str]] = []
    for r in all_records:
        wid = r.get("wikidata_id", "")
        if wid and wid not in seen:
            seen.add(wid)
            unique.append(r)
        elif not wid:
            unique.append(r)
    
    # CSV output
    csv_path = OUTPUT_DIR / "wikidata_businesses.csv"
    
    # Collect all possible fieldnames
    all_fields: set[str] = set()
    for r in unique:
        all_fields.update(r.keys())
    
    # Order the fields nicely
    priority_fields = [
        "wikidata_id", "name", "description", "category", "subcategory",
        "industry", "city", "source_query", "source",
    ]
    extra_fields: list[str] = sorted(all_fields - set(priority_fields))
    fieldnames: list[str] = priority_fields + extra_fields
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(unique)
    
    print(f"\n  💾 Saved {len(unique):,} unique records to: {csv_path}")
    
    # JSON raw dump
    json_path = RAW_DIR / "wikidata_raw.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(unique, f, indent=2, ensure_ascii=False)
    
    # Stats
    cats: defaultdict[str, int] = defaultdict(int)
    subcats: defaultdict[str, int] = defaultdict(int)
    for r in unique:
        cats[r["category"]] += 1
        subcats[r["subcategory"]] += 1
    
    print("\n  📊 Category distribution:")
    for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"    {cat:<30} {count:>6,}")
    
    print("\n  📊 Subcategory distribution:")
    for sub, count in sorted(subcats.items(), key=lambda x: -x[1]):
        print(f"    {sub:<30} {count:>6,}")


def main() -> None:
    print("=" * 60)
    print("WIKIDATA SPARQL QUERY — INDIAN BUSINESSES")
    print("=" * 60)
    print("  Endpoint:", SPARQL_ENDPOINT)
    print("  Queries:", len(QUERIES))
    print("  Cost: $0 (Wikidata is free)")
    
    # Select queries to run
    import sys
    if len(sys.argv) > 1:
        selected = sys.argv[1:]
        queries = {k: v for k, v in QUERIES.items() if k in selected}
        if not queries:
            print(f"\n❌ No matching queries. Available: {', '.join(QUERIES.keys())}")
            return
    else:
        queries = QUERIES
    
    print(f"\n  Running {len(queries)} queries...")
    
    all_records: list[dict[str, str]] = []
    
    for query_name, sparql in queries.items():
        results = run_sparql_query(query_name, sparql)
        records = process_results(query_name, results)
        all_records.extend(records)
        
        # Be polite to Wikidata
        time.sleep(3)
    
    save_all(all_records)
    
    print(f"\n✅ Done! Total records: {len(all_records):,}")


if __name__ == "__main__":
    main()
