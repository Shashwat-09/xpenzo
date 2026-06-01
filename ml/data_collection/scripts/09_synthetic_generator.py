#!/usr/bin/env python3
"""
09_synthetic_generator.py — Xpenzo Synthetic Data Generator

Generates synthetic merchant records for:
  1. 109 unused L3 categories (no real data exists)
  2. 239 low-count L3 categories (<50 records)

Uses taxonomy keywords[] and example_merchants[] to create realistic
merchant names with augmentation (typos, abbreviations, transliterations,
case variations, truncations).

Augmentation strategies (from docs/09 Section 13.2):
  - Truncation (SMS cuts merchant names)
  - Abbreviation (UPI shortens names)
  - Typo injection (swap/insert/delete chars)
  - Case variations (UPPER, lower, Title)
  - Hindi transliteration variants
  - Common spelling alternatives
  - City/state suffix variations

Output: ml/data_collection/labeled/synthetic_dataset.csv
        ml/data_collection/labeled/synthetic_stats.json

Usage:
    python 09_synthetic_generator.py [--output-dir PATH]
           [--min-per-category 200] [--augmentation-factor 5]
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent
TAXONOMY_PATH = PROJECT_ROOT / "ml" / "taxonomy" / "category_taxonomy.json"
LABELED_PATH = PROJECT_ROOT / "ml" / "data_collection" / "labeled" / "labeled_dataset.csv"
UNUSED_PATH = PROJECT_ROOT / "ml" / "data_collection" / "labeled" / "_unused_l3.json"
LOW_COUNT_PATH = PROJECT_ROOT / "ml" / "data_collection" / "labeled" / "_low_count_l3.json"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "ml" / "data_collection" / "labeled"

# ---------------------------------------------------------------------------
# Indian geographic data for realistic records
# ---------------------------------------------------------------------------
INDIAN_CITIES: list[dict[str, str | float]] = [
    {"city": "Mumbai", "state": "Maharashtra", "lat": 19.076, "lon": 72.877},
    {"city": "Delhi", "state": "Delhi", "lat": 28.704, "lon": 77.102},
    {"city": "Bengaluru", "state": "Karnataka", "lat": 12.972, "lon": 77.594},
    {"city": "Hyderabad", "state": "Telangana", "lat": 17.385, "lon": 78.487},
    {"city": "Chennai", "state": "Tamil Nadu", "lat": 13.083, "lon": 80.270},
    {"city": "Kolkata", "state": "West Bengal", "lat": 22.573, "lon": 88.364},
    {"city": "Pune", "state": "Maharashtra", "lat": 18.520, "lon": 73.857},
    {"city": "Ahmedabad", "state": "Gujarat", "lat": 23.023, "lon": 72.571},
    {"city": "Jaipur", "state": "Rajasthan", "lat": 26.912, "lon": 75.787},
    {"city": "Lucknow", "state": "Uttar Pradesh", "lat": 26.847, "lon": 80.947},
    {"city": "Kochi", "state": "Kerala", "lat": 9.932, "lon": 76.267},
    {"city": "Chandigarh", "state": "Chandigarh", "lat": 30.734, "lon": 76.769},
    {"city": "Indore", "state": "Madhya Pradesh", "lat": 22.720, "lon": 75.858},
    {"city": "Bhopal", "state": "Madhya Pradesh", "lat": 23.260, "lon": 77.413},
    {"city": "Patna", "state": "Bihar", "lat": 25.612, "lon": 85.145},
    {"city": "Nagpur", "state": "Maharashtra", "lat": 21.146, "lon": 79.088},
    {"city": "Coimbatore", "state": "Tamil Nadu", "lat": 11.017, "lon": 76.956},
    {"city": "Visakhapatnam", "state": "Andhra Pradesh", "lat": 17.687, "lon": 83.218},
    {"city": "Guwahati", "state": "Assam", "lat": 26.144, "lon": 91.736},
    {"city": "Thiruvananthapuram", "state": "Kerala", "lat": 8.524, "lon": 76.936},
    {"city": "Surat", "state": "Gujarat", "lat": 21.170, "lon": 72.831},
    {"city": "Varanasi", "state": "Uttar Pradesh", "lat": 25.318, "lon": 83.010},
    {"city": "Bhubaneswar", "state": "Odisha", "lat": 20.297, "lon": 85.825},
    {"city": "Ranchi", "state": "Jharkhand", "lat": 23.344, "lon": 85.310},
    {"city": "Dehradun", "state": "Uttarakhand", "lat": 30.317, "lon": 78.032},
]

# Indian person name prefixes for business names
NAME_PREFIXES: list[str] = [
    "Sharma", "Gupta", "Kumar", "Singh", "Patel", "Jain", "Agarwal",
    "Verma", "Reddy", "Rao", "Nair", "Pillai", "Das", "Mukherjee",
    "Chatterjee", "Iyer", "Menon", "Bhat", "Deshmukh", "Kulkarni",
    "Thakur", "Yadav", "Mishra", "Tiwari", "Pandey", "Srivastava",
    "Bansal", "Mahajan", "Kapoor", "Malhotra", "Arora", "Mehra",
]

# Common business suffixes by rough domain
BUSINESS_SUFFIXES: dict[str, list[str]] = {
    "healthcare": ["Hospital", "Clinic", "Medical Centre", "Health Care", "Nursing Home", "Diagnostics"],
    "food": ["Restaurant", "Dhaba", "Kitchen", "Foods", "Caterers", "Cafe", "Meals"],
    "shopping": ["Store", "Shop", "Mart", "Emporium", "Traders", "Enterprises", "Point"],
    "education": ["Academy", "School", "Institute", "Classes", "Coaching", "Tutorial", "College"],
    "services": ["Services", "Solutions", "Associates", "Consultant", "Agency", "Works"],
    "finance": ["Finance", "Capital", "Investments", "Insurance", "Loans"],
    "transport": ["Motors", "Auto", "Cabs", "Travels", "Transport"],
    "tech": ["Technologies", "Tech", "Software", "IT Solutions", "Digital"],
    "generic": ["Pvt Ltd", "LLP", "& Co", "Group", "Hub", "Zone", "World", "Palace"],
}


# ═══════════════════════════════════════════════════════════════════════════
# AUGMENTATION ENGINE (per docs/09 Section 13.2)
# ═══════════════════════════════════════════════════════════════════════════

def inject_random_typo(name: str) -> str:
    """Inject a single random typo: swap, insert, or delete a character."""
    if len(name) < 3:
        return name
    chars = list(name)
    op = random.choice(["swap", "insert", "delete"])
    idx = random.randint(1, len(chars) - 2)

    if op == "swap" and idx < len(chars) - 1:
        chars[idx], chars[idx + 1] = chars[idx + 1], chars[idx]
    elif op == "insert":
        chars.insert(idx, random.choice("aeiounrstl"))
    elif op == "delete":
        chars.pop(idx)

    return "".join(chars)


# Hindi transliteration variant mappings
HINDI_VARIANTS: dict[str, list[str]] = {
    "punjabi": ["panjabi", "pnjabi"],
    "dhaba": ["dhabba", "dhab"],
    "restaurant": ["restraunt", "restarant", "restro", "restaurnt"],
    "hospital": ["hosptal", "hosptl", "hospitl"],
    "pharmacy": ["pharmcy", "farmacy", "pharma"],
    "school": ["skool", "schl"],
    "college": ["colg", "collge"],
    "medical": ["medcl", "medikal", "medicl"],
    "clinic": ["clinik", "clnic"],
    "hotel": ["hotl", "hotell"],
    "mart": ["mrt"],
    "store": ["stor", "stoer"],
    "super": ["supr", "spr"],
    "market": ["mrkt", "markt"],
    "centre": ["center", "centr", "sentr"],
    "service": ["servce", "srvice", "servis"],
    "enterprises": ["enterpr", "entrprs", "enterprs"],
    "traders": ["trdrs", "tradrs"],
    "boutique": ["butique", "boutiqe"],
    "salon": ["saloon", "saln"],
    "gym": ["jym", "jimm"],
    "yoga": ["yog"],
    "studio": ["stdio", "stuidio"],
    "fitness": ["fitnes", "fitns"],
    "academy": ["acadmy", "acdmy"],
    "institute": ["instt", "insttute"],
    "diagnostic": ["diagnstc", "diagnstic"],
    "laboratory": ["lab", "labb"],
    "insurance": ["insuranc", "insurnce"],
    "investment": ["invstmnt", "investmnt"],
}


def hindi_transliterate_variants(name: str) -> list[str]:
    """Generate Hindi transliteration variants from known patterns."""
    variants: list[str] = []
    name_lower = name.lower()
    for word, alts in HINDI_VARIANTS.items():
        if word in name_lower:
            for alt in alts:
                variants.append(name_lower.replace(word, alt))
    return variants


def spelling_alternatives(name: str) -> list[str]:
    """Generate common spelling alternatives."""
    variants: list[str] = []
    replacements: list[tuple[str, str]] = [
        ("ph", "f"), ("tion", "shun"), ("sion", "shun"),
        ("oo", "u"), ("ee", "i"), ("ck", "k"),
        ("ight", "ite"), ("ough", "uf"),
    ]
    name_lower = name.lower()
    for old, new in replacements:
        if old in name_lower:
            variants.append(name_lower.replace(old, new, 1))
    return variants


def augment_merchant_name(name: str, factor: int = 5) -> list[str]:
    """
    Generate realistic noisy variants of a merchant name.
    Simulates real-world SMS truncation, typos, and abbreviations.
    Returns at most `factor` unique variants (including original).
    """
    variants: set[str] = {name}

    # 1. Truncation (SMS often cuts merchant names)
    if len(name) > 15:
        variants.add(name[:15])
        variants.add(name[:20])
    if len(name) > 10:
        variants.add(name[:12])

    # 2. Abbreviation (common in UPI)
    words = name.split()
    if len(words) > 1:
        variants.add("".join(w[0].upper() for w in words if w))
        variants.add(words[0] + " " + " ".join(w[0].upper() for w in words[1:] if w))
        if len(words) > 2:
            variants.add(words[0] + " " + words[-1])

    # 3. Typo injection
    for _ in range(3):
        variants.add(inject_random_typo(name))

    # 4. Case variations
    variants.add(name.upper())
    variants.add(name.lower())
    variants.add(name.title())

    # 5. Hindi transliteration variants
    for v in hindi_transliterate_variants(name):
        variants.add(v)

    # 6. Common spelling alternatives
    for v in spelling_alternatives(name):
        variants.add(v)

    # 7. Strip common suffixes/prefixes
    for suffix in ["pvt ltd", "private limited", "llp", "& co", "(india)"]:
        if name.lower().endswith(suffix):
            stripped = name[: -len(suffix)].strip()
            if stripped:
                variants.add(stripped)

    result = list(variants)
    random.shuffle(result)
    return result[:factor]


# ═══════════════════════════════════════════════════════════════════════════
# MERCHANT NAME GENERATOR
# ═══════════════════════════════════════════════════════════════════════════

def get_domain_for_l1(l1_code: str) -> str:
    """Map L1 code to business suffix domain."""
    domain_map: dict[str, str] = {
        "FD": "food", "TR": "transport", "SH": "shopping", "HC": "healthcare",
        "FI": "finance", "ED": "education", "EN": "generic", "UT": "services",
        "TC": "tech", "TV": "generic", "GV": "services", "PC": "services",
        "FS": "generic", "PS": "services", "MS": "generic",
    }
    return domain_map.get(l1_code, "generic")


def generate_base_names(
    l3_info: dict[str, Any],
    count: int,
) -> list[str]:
    """
    Generate `count` unique base merchant names from taxonomy keywords
    and example_merchants, combined with Indian name prefixes.
    """
    keywords: list[str] = l3_info.get("keywords", [])
    merchants: list[str] = l3_info.get("merchants", [])
    l1_code: str = str(l3_info.get("l1_code", "MS"))
    l3_name: str = str(l3_info.get("l3_name", ""))
    domain = get_domain_for_l1(l1_code)
    suffixes = BUSINESS_SUFFIXES.get(domain, BUSINESS_SUFFIXES["generic"])

    names: set[str] = set()

    # Add known merchants directly
    for m in merchants:
        names.add(m)

    # Generate from keywords + name prefixes + suffixes
    for kw in keywords:
        names.add(kw.title())
        for prefix in random.sample(NAME_PREFIXES, min(5, len(NAME_PREFIXES))):
            names.add(f"{prefix}'s {kw.title()}")
            names.add(f"{prefix} {kw.title()}")
        for suffix in random.sample(suffixes, min(3, len(suffixes))):
            names.add(f"{kw.title()} {suffix}")
        for prefix in random.sample(NAME_PREFIXES, min(3, len(NAME_PREFIXES))):
            for suffix in random.sample(suffixes, min(2, len(suffixes))):
                names.add(f"{prefix} {kw.title()} {suffix}")

    # Generate from L3 name itself
    names.add(l3_name)
    for prefix in random.sample(NAME_PREFIXES, min(5, len(NAME_PREFIXES))):
        names.add(f"{prefix} {l3_name}")

    # If still not enough, create more variations
    while len(names) < count:
        prefix = random.choice(NAME_PREFIXES)
        if keywords:
            kw = random.choice(keywords)
            suffix = random.choice(suffixes)
            names.add(f"{prefix} {kw.title()} {suffix}")
        else:
            names.add(f"{prefix} {l3_name} {random.choice(suffixes)}")

    return list(names)[:count]


# ═══════════════════════════════════════════════════════════════════════════
# SYNTHETIC RECORD GENERATOR
# ═══════════════════════════════════════════════════════════════════════════

OUTPUT_FIELDS: list[str] = [
    "name", "brand", "category", "subcategory", "osm_tag", "cuisine",
    "city", "state", "lat", "lon", "phone", "website",
    "l1_id", "l1_code", "l1_name",
    "l2_id", "l2_code", "l2_name",
    "l3_id", "l3_code", "l3_name",
    "confidence", "match_method",
]


def generate_records_for_category(
    l3_info: dict[str, Any],
    target_count: int,
    augmentation_factor: int,
) -> list[dict[str, str]]:
    """Generate synthetic records for one L3 category."""
    # How many base names do we need?
    base_needed = max(10, math.ceil(target_count / augmentation_factor))
    base_names = generate_base_names(l3_info, base_needed)

    records: list[dict[str, str]] = []

    for base_name in base_names:
        variants = augment_merchant_name(base_name, augmentation_factor)
        for variant in variants:
            city_info = random.choice(INDIAN_CITIES)
            lat_jitter = random.uniform(-0.05, 0.05)
            lon_jitter = random.uniform(-0.05, 0.05)

            record: dict[str, str] = {
                "name": variant,
                "brand": "",
                "category": str(l3_info.get("l1_name", "")),
                "subcategory": str(l3_info.get("l2_name", "")),
                "osm_tag": "",
                "cuisine": "",
                "city": str(city_info["city"]),
                "state": str(city_info["state"]),
                "lat": str(round(float(city_info["lat"]) + lat_jitter, 6)),
                "lon": str(round(float(city_info["lon"]) + lon_jitter, 6)),
                "phone": "",
                "website": "",
                "l1_id": str(l3_info.get("l1_id", "")),
                "l1_code": str(l3_info.get("l1_code", "")),
                "l1_name": str(l3_info.get("l1_name", "")),
                "l2_id": str(l3_info.get("l2_id", "")),
                "l2_code": str(l3_info.get("l2_code", "")),
                "l2_name": str(l3_info.get("l2_name", "")),
                "l3_id": str(l3_info.get("l3_id", "")),
                "l3_code": str(l3_info.get("l3_code", "")),
                "l3_name": str(l3_info.get("l3_name", "")),
                "confidence": "1.00",
                "match_method": "synthetic",
            }
            records.append(record)

            if len(records) >= target_count:
                return records

    return records


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(description="Xpenzo Synthetic Data Generator")
    parser.add_argument(
        "--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for output",
    )
    parser.add_argument(
        "--min-per-category", type=int, default=200,
        help="Minimum records per L3 category (default: 200)",
    )
    parser.add_argument(
        "--augmentation-factor", type=int, default=5,
        help="Augmentation variants per base name (default: 5)",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for reproducibility",
    )
    args = parser.parse_args()

    random.seed(args.seed)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_csv = output_dir / "synthetic_dataset.csv"
    output_stats = output_dir / "synthetic_stats.json"
    min_per_cat: int = args.min_per_category
    aug_factor: int = args.augmentation_factor

    # ── Load taxonomy ─────────────────────────────────────────────────
    print(f"Loading taxonomy from {TAXONOMY_PATH} ...")
    with open(TAXONOMY_PATH, "r", encoding="utf-8") as f:
        tax_data: dict[str, Any] = json.load(f)

    # Build full L3 info index
    l3_index: dict[str, dict[str, Any]] = {}
    for l1 in tax_data["categories"]:
        for l2 in l1["subcategories"]:
            for l3 in l2["micro_categories"]:
                l3_index[l3["l3_code"]] = {
                    "l3_id": l3["l3_id"],
                    "l3_code": l3["l3_code"],
                    "l3_name": l3["l3_name"],
                    "l2_id": l2["l2_id"],
                    "l2_code": l2["l2_code"],
                    "l2_name": l2["l2_name"],
                    "l1_id": l1["l1_id"],
                    "l1_code": l1["l1_code"],
                    "l1_name": l1["l1_name"],
                    "keywords": l3.get("keywords", []),
                    "merchants": l3.get("example_merchants", []),
                }
    print(f"  {len(l3_index)} L3 categories loaded")

    # ── Count existing records per L3 ─────────────────────────────────
    print(f"\nCounting existing records from {LABELED_PATH} ...")
    existing_counts: dict[str, int] = defaultdict(int)
    with open(LABELED_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing_counts[row["l3_code"]] += 1
    total_existing = sum(existing_counts.values())
    print(f"  {total_existing:,} existing records across {len(existing_counts)} L3 categories")

    # ── Identify categories needing synthetic data ────────────────────
    categories_to_generate: list[tuple[str, int]] = []
    for code, info in l3_index.items():
        current = existing_counts.get(code, 0)
        if current < min_per_cat:
            needed = min_per_cat - current
            categories_to_generate.append((code, needed))

    categories_to_generate.sort(key=lambda x: x[1], reverse=True)

    unused_count = sum(1 for code, _ in categories_to_generate if existing_counts.get(code, 0) == 0)
    low_count = sum(1 for code, _ in categories_to_generate if 0 < existing_counts.get(code, 0) < min_per_cat)

    print(f"\n  Categories needing synthetic data: {len(categories_to_generate)}")
    print(f"    Completely unused (0 records): {unused_count}")
    print(f"    Low count (1-{min_per_cat - 1} records):   {low_count}")
    total_needed = sum(n for _, n in categories_to_generate)
    print(f"    Total synthetic records needed: {total_needed:,}")

    # ── Generate synthetic data ───────────────────────────────────────
    print(f"\nGenerating synthetic records (aug_factor={aug_factor}) ...")
    t0 = time.time()
    all_synthetic: list[dict[str, str]] = []
    gen_stats: dict[str, int] = {}

    for i, (code, needed) in enumerate(categories_to_generate):
        info = l3_index[code]
        records = generate_records_for_category(info, needed, aug_factor)
        all_synthetic.extend(records)
        gen_stats[code] = len(records)

        if (i + 1) % 50 == 0:
            elapsed = time.time() - t0
            print(f"  {i + 1:>4} / {len(categories_to_generate)}  "
                  f"({len(all_synthetic):,} records, {elapsed:.1f}s)")

    elapsed = time.time() - t0
    print(f"  Done: {len(all_synthetic):,} synthetic records in {elapsed:.1f}s")

    # ── Write synthetic CSV ───────────────────────────────────────────
    print(f"\nWriting synthetic CSV to {output_csv} ...")
    with open(output_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(all_synthetic)
    size_mb = output_csv.stat().st_size / (1024 * 1024)
    print(f"  Written: {size_mb:.1f} MB ({len(all_synthetic):,} records)")

    # ── Stats ─────────────────────────────────────────────────────────
    by_l1: defaultdict[str, int] = defaultdict(int)
    for record in all_synthetic:
        by_l1[record["l1_name"]] += 1

    stats: dict[str, Any] = {
        "total_synthetic_records": len(all_synthetic),
        "categories_filled": len(categories_to_generate),
        "previously_unused_filled": unused_count,
        "low_count_boosted": low_count,
        "min_per_category_target": min_per_cat,
        "augmentation_factor": aug_factor,
        "l1_distribution": dict(sorted(by_l1.items(), key=lambda x: x[1], reverse=True)),
        "top_30_generated": dict(
            sorted(gen_stats.items(), key=lambda x: x[1], reverse=True)[:30]
        ),
    }

    with open(output_stats, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    # ── Summary ───────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("SYNTHETIC GENERATION COMPLETE")
    print("=" * 60)
    print(f"  Synthetic records:     {stats['total_synthetic_records']:,}")
    print(f"  Categories filled:     {stats['categories_filled']}")
    print(f"  Previously unused:     {stats['previously_unused_filled']}")
    print(f"  Low count boosted:     {stats['low_count_boosted']}")
    print(f"\n  L1 distribution of synthetic data:")
    for l1_name, count in sorted(by_l1.items(), key=lambda x: x[1], reverse=True):
        print(f"    {l1_name:35s} {count:>6,}")

    print(f"\n  Combined dataset size:")
    print(f"    Existing:  {total_existing:>10,}")
    print(f"    Synthetic: {len(all_synthetic):>10,}")
    print(f"    Total:     {total_existing + len(all_synthetic):>10,}")

    print(f"\n  Output files:")
    print(f"    {output_csv}")
    print(f"    {output_stats}")


if __name__ == "__main__":
    main()
