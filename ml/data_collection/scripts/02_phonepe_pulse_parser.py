"""
PhonePe Pulse Data Parser
Extracts UPI transaction patterns, top merchants by category, state-wise data
from the cloned PhonePe Pulse repository.

No external dependencies needed (uses stdlib json, csv, os).
Source: Cloned repo at raw/phonepe_pulse/
Output: CSV files in processed/
"""

import json
import csv
from pathlib import Path
from collections import defaultdict
from typing import Any

SCRIPT_DIR = Path(__file__).parent
PULSE_DIR = SCRIPT_DIR.parent / "raw" / "phonepe_pulse" / "data"
OUTPUT_DIR = SCRIPT_DIR.parent / "processed"


def load_json_files(base_path: str | Path) -> list[dict[str, Any]]:
    """Recursively load all JSON files from a directory."""
    results: list[dict[str, Any]] = []
    base = Path(base_path)
    if not base.exists():
        print(f"  Warning: Path not found: {base}")
        return results
    
    for json_file in sorted(base.rglob("*.json")):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Extract year/quarter from path
            parts = json_file.relative_to(base).parts
            results.append({
                "file": str(json_file.relative_to(base)),
                "parts": parts,
                "data": data
            })
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"  Error reading {json_file}: {e}")
    
    return results


def parse_aggregated_transactions() -> list[dict[str, Any]]:
    """Parse aggregated transaction data (by type: Merchant, P2P, etc.)."""
    print("\n📊 Parsing aggregated transaction data...")
    
    base = PULSE_DIR / "aggregated" / "transaction" / "country" / "india"
    if not base.exists():
        print(f"  Not found: {base}")
        return []
    
    rows: list[dict[str, Any]] = []
    
    # National level data
    for year_dir in sorted(base.iterdir()):
        if year_dir.name == "state" or not year_dir.is_dir():
            continue
        year = year_dir.name
        
        for quarter_file in sorted(year_dir.glob("*.json")):
            quarter = quarter_file.stem
            try:
                with open(quarter_file, 'r') as f:
                    data = json.load(f)
                
                if data.get("success") and data.get("data", {}).get("transactionData"):
                    for txn in data["data"]["transactionData"]:
                        for pi in txn.get("paymentInstruments", []):
                            rows.append({
                                "year": year,
                                "quarter": f"Q{quarter}",
                                "level": "national",
                                "state": "india",
                                "type": txn["name"],
                                "count": pi.get("count", 0),
                                "amount": pi.get("amount", 0),
                            })
            except Exception as e:
                print(f"  Error: {quarter_file}: {e}")
    
    # State level data
    state_dir = base / "state"
    if state_dir.exists():
        for state_path in sorted(state_dir.iterdir()):
            if not state_path.is_dir():
                continue
            state_name = state_path.name
            
            for year_dir in sorted(state_path.iterdir()):
                if not year_dir.is_dir():
                    continue
                year = year_dir.name
                
                for quarter_file in sorted(year_dir.glob("*.json")):
                    quarter = quarter_file.stem
                    try:
                        with open(quarter_file, 'r') as f:
                            data = json.load(f)
                        
                        if data.get("success") and data.get("data", {}).get("transactionData"):
                            for txn in data["data"]["transactionData"]:
                                for pi in txn.get("paymentInstruments", []):
                                    rows.append({
                                        "year": year,
                                        "quarter": f"Q{quarter}",
                                        "level": "state",
                                        "state": state_name,
                                        "type": txn["name"],
                                        "count": pi.get("count", 0),
                                        "amount": pi.get("amount", 0),
                                    })
                    except Exception as e:
                        pass
    
    print(f"  Extracted {len(rows):,} transaction records")
    return rows


def parse_top_transactions() -> list[dict[str, Any]]:
    """Parse top transactions data (states, districts, pincodes)."""
    print("\n📊 Parsing top transaction data...")
    
    base = PULSE_DIR / "top" / "transaction" / "country" / "india"
    if not base.exists():
        print(f"  Not found: {base}")
        return []
    
    rows: list[dict[str, Any]] = []
    
    # National level top data
    for year_dir in sorted(base.iterdir()):
        if year_dir.name == "state" or not year_dir.is_dir():
            continue
        year = year_dir.name
        
        for quarter_file in sorted(year_dir.glob("*.json")):
            quarter = quarter_file.stem
            try:
                with open(quarter_file, 'r') as f:
                    data = json.load(f)
                
                if not data.get("success"):
                    continue
                
                d = data.get("data", {})
                
                # Top states
                for item in d.get("states", []):
                    metric = item.get("metric", {})
                    rows.append({
                        "year": year,
                        "quarter": f"Q{quarter}",
                        "entity_type": "state",
                        "entity_name": item.get("entityName", ""),
                        "count": metric.get("count", 0),
                        "amount": metric.get("amount", 0),
                    })
                
                # Top districts
                for item in d.get("districts", []):
                    metric = item.get("metric", {})
                    rows.append({
                        "year": year,
                        "quarter": f"Q{quarter}",
                        "entity_type": "district",
                        "entity_name": item.get("entityName", ""),
                        "count": metric.get("count", 0),
                        "amount": metric.get("amount", 0),
                    })
                
                # Top pincodes
                for item in d.get("pincodes", []):
                    metric = item.get("metric", {})
                    rows.append({
                        "year": year,
                        "quarter": f"Q{quarter}",
                        "entity_type": "pincode",
                        "entity_name": str(item.get("entityName", "")),
                        "count": metric.get("count", 0),
                        "amount": metric.get("amount", 0),
                    })
            except Exception:
                pass
    
    print(f"  Extracted {len(rows):,} top entity records")
    return rows


def parse_user_data() -> list[dict[str, Any]]:
    """Parse user registration/app data."""
    print("\n📊 Parsing user data...")
    
    base = PULSE_DIR / "aggregated" / "user" / "country" / "india"
    if not base.exists():
        print(f"  Not found: {base}")
        return []
    
    rows: list[dict[str, Any]] = []
    
    for year_dir in sorted(base.iterdir()):
        if year_dir.name == "state" or not year_dir.is_dir():
            continue
        year = year_dir.name
        
        for quarter_file in sorted(year_dir.glob("*.json")):
            quarter = quarter_file.stem
            try:
                with open(quarter_file, 'r') as f:
                    data = json.load(f)
                
                if not data.get("success"):
                    continue
                
                d = data.get("data", {})
                agg = d.get("aggregated", {})
                
                rows.append({
                    "year": year,
                    "quarter": f"Q{quarter}",
                    "registered_users": agg.get("registeredUsers", 0),
                    "app_opens": agg.get("appOpens", 0),
                })
                
                # Per-brand data
                devices: list[Any] = d.get("usersByDevice", []) or []
                for brand in devices:
                    rows.append({
                        "year": year,
                        "quarter": f"Q{quarter}",
                        "device_brand": brand.get("brand", ""),
                        "device_count": brand.get("count", 0),
                        "device_percentage": brand.get("percentage", 0),
                    })
            except Exception:
                pass
    
    print(f"  Extracted {len(rows):,} user records")
    return rows


def parse_insurance_data() -> list[dict[str, Any]]:
    """Parse insurance transaction data."""
    print("\n📊 Parsing insurance data...")
    
    base = PULSE_DIR / "aggregated" / "insurance" / "country" / "india"
    if not base.exists():
        print(f"  Not found: {base}")
        return []
    
    rows: list[dict[str, Any]] = []
    
    for year_dir in sorted(base.iterdir()):
        if year_dir.name == "state" or not year_dir.is_dir():
            continue
        year = year_dir.name
        
        for quarter_file in sorted(year_dir.glob("*.json")):
            quarter = quarter_file.stem
            try:
                with open(quarter_file, 'r') as f:
                    data = json.load(f)
                
                if data.get("success") and data.get("data", {}).get("transactionData"):
                    for txn in data["data"]["transactionData"]:
                        for pi in txn.get("paymentInstruments", []):
                            rows.append({
                                "year": year,
                                "quarter": f"Q{quarter}",
                                "type": txn.get("name", ""),
                                "count": pi.get("count", 0),
                                "amount": pi.get("amount", 0),
                            })
            except Exception:
                pass
    
    print(f"  Extracted {len(rows):,} insurance records")
    return rows


def save_csv(rows: list[dict[str, Any]], filename: str, fieldnames: list[str] | None = None) -> None:
    """Save list of dicts to CSV."""
    if not rows:
        print(f"  No data to save for {filename}")
        return
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filepath = OUTPUT_DIR / filename
    
    if fieldnames is None:
        fieldnames = list(rows[0].keys())
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"  Saved {len(rows):,} rows to: {filepath}")


def generate_transaction_type_summary(txn_rows: list[dict[str, Any]]) -> defaultdict[str, dict[str, Any]]:
    """Generate summary of transaction types useful for ML categorization."""
    print("\n📈 Generating transaction type summary...")
    
    type_totals: defaultdict[str, dict[str, Any]] = defaultdict(lambda: {"count": 0, "amount": 0})
    
    for row in txn_rows:
        if row["level"] == "national":
            key = row["type"]
            type_totals[key]["count"] += row["count"]
            type_totals[key]["amount"] += row["amount"]
    
    print("\n  UPI Transaction Types (all-time national totals):")
    print(f"  {'Type':<30} {'Count':>15} {'Amount (₹ Cr)':>18}")
    print("  " + "-" * 65)
    for ttype, vals in sorted(type_totals.items(), key=lambda x: -x[1]["count"]):
        count_str = f"{vals['count']:,}"
        amount_cr = vals['amount'] / 1e7
        amount_str = f"{amount_cr:,.0f}"
        print(f"  {ttype:<30} {count_str:>15} {amount_str:>18}")
    
    return type_totals


def generate_state_rankings(top_rows: list[dict[str, Any]]) -> None:
    """Generate state-wise transaction rankings."""
    print("\n📈 Generating state rankings...")
    
    state_totals: defaultdict[str, dict[str, Any]] = defaultdict(lambda: {"count": 0, "amount": 0})
    
    for row in top_rows:
        if row["entity_type"] == "state":
            key = row["entity_name"]
            state_totals[key]["count"] += row["count"]
            state_totals[key]["amount"] += row["amount"]
    
    print(f"\n  Top 15 states by UPI transaction volume:")
    print(f"  {'State':<25} {'Count':>15} {'Amount (₹ Cr)':>18}")
    print("  " + "-" * 60)
    for state, vals in sorted(state_totals.items(), key=lambda x: -x[1]["count"])[:15]:
        count_str = f"{vals['count']:,}"
        amount_cr = vals['amount'] / 1e7
        amount_str = f"{amount_cr:,.0f}"
        print(f"  {state:<25} {count_str:>15} {amount_str:>18}")


def main() -> None:
    print("=" * 60)
    print("PHONEPE PULSE DATA PARSER")
    print("=" * 60)
    
    if not PULSE_DIR.exists():
        print(f"ERROR: PhonePe Pulse data not found at: {PULSE_DIR}")
        print("Run: git clone https://github.com/PhonePe/pulse.git raw/phonepe_pulse/")
        return
    
    # Parse all data types
    txn_rows = parse_aggregated_transactions()
    top_rows = parse_top_transactions()
    user_rows = parse_user_data()
    insurance_rows = parse_insurance_data()
    
    # Save to CSV
    save_csv(txn_rows, "phonepe_transactions.csv")
    save_csv(top_rows, "phonepe_top_entities.csv")
    save_csv(user_rows, "phonepe_users.csv")
    save_csv(insurance_rows, "phonepe_insurance.csv")
    
    # Generate summaries
    if txn_rows:
        generate_transaction_type_summary(txn_rows)
    if top_rows:
        generate_state_rankings(top_rows)
    
    # Key insights for ML
    print("\n" + "=" * 60)
    print("KEY INSIGHTS FOR ML MODEL")
    print("=" * 60)
    print("""
    PhonePe Pulse data provides:
    1. Transaction TYPE distribution (Merchant vs P2P vs Recharge vs Financial)
       → Useful for Amount-Time Pattern (ATP) bucket calibration
    2. State-wise transaction volumes
       → Useful for regional category weight adjustments
    3. Temporal patterns (quarter-over-quarter growth)
       → Useful for seasonality features in the ML model
    4. Device brand distribution
       → Useful for understanding target user demographics
    
    NOTE: This data does NOT contain individual merchant names.
    For merchant names, use OSM, Google Maps, and web scraping data.
    """)
    
    print("✅ Done!")


if __name__ == "__main__":
    main()
