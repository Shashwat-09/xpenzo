"""
Master Data Collection Pipeline — Orchestrator
Runs all data collection scripts in sequence, merges outputs,
deduplicates, and generates statistics.

Usage:
  python 07_master_pipeline.py                  # Run everything
  python 07_master_pipeline.py --skip-download  # Only merge existing data
  python 07_master_pipeline.py --only osm phonepe wikidata  # Run specific scripts

Dependencies: pip install pandas tqdm requests osmium  (+ others per script)

Output:
  processed/master_dataset.csv        — merged & deduplicated
  processed/master_stats.json         — statistics summary
  processed/per_source/*.csv          — individual script outputs
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
RAW_DIR = BASE_DIR / "raw"
PROCESSED_DIR = BASE_DIR / "processed"
LABELED_DIR = BASE_DIR / "labeled"

# ── Pipeline Steps ───────────────────────────────────────

PIPELINE_STEPS: list[dict[str, Any]] = [
    {
        "id": "phonepe",
        "name": "PhonePe Pulse Parser",
        "script": "02_phonepe_pulse_parser.py",
        "description": "Parse PhonePe Pulse transaction data",
        "requires_download": False,
        "expected_output": "phonepe_transactions.csv",
        "priority": 1,
    },
    {
        "id": "wikidata",
        "name": "Wikidata SPARQL",
        "script": "06_wikidata_query.py",
        "description": "Query Wikidata for Indian businesses",
        "requires_download": False,  # No file download, just API
        "expected_output": "wikidata_businesses.csv",
        "priority": 2,
    },
    {
        "id": "osm",
        "name": "OSM India Extractor",
        "script": "01_osm_extractor.py",
        "description": "Download & extract businesses from OpenStreetMap (~1.5GB download)",
        "requires_download": True,
        "expected_output": "osm_india_businesses.csv",
        "priority": 3,
    },
    {
        "id": "datagov",
        "name": "data.gov.in Downloader",
        "script": "04_data_gov_downloader.py",
        "description": "Download government open data (MSME, FSSAI, etc.)",
        "requires_download": True,
        "expected_output": None,  # Multiple outputs
        "priority": 4,
    },
    {
        "id": "scrapers",
        "name": "Web Scrapers",
        "script": "03_web_scrapers.py",
        "description": "Scrape Swiggy, Zomato, Practo, JustDial, Sulekha",
        "requires_download": False,
        "expected_output": "scraped_all_merged.csv",
        "priority": 5,
    },
    {
        "id": "google",
        "name": "Google Maps API",
        "script": "05_google_maps_api.py",
        "description": "Google Maps Places API (requires API key)",
        "requires_download": False,
        "expected_output": "google_maps_businesses.csv",
        "priority": 6,
    },
]


def run_script(step: dict[str, Any], dry_run: bool = False) -> bool:
    """Run a pipeline step as a subprocess."""
    script_path: Path = SCRIPT_DIR / step["script"]
    
    if not script_path.exists():
        print(f"  ❌ Script not found: {script_path}")
        return False
    
    if dry_run:
        print(f"  [DRY RUN] Would run: {step['script']}")
        return True
    
    print(f"\n{'─' * 50}")
    print(f"  ▶ Running: {step['name']}")
    print(f"    Script:  {step['script']}")
    print(f"    Desc:    {step['description']}")
    print(f"{'─' * 50}")
    
    start = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(SCRIPT_DIR),
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour max per script
        )
        
        elapsed = time.time() - start
        
        if result.returncode == 0:
            print(f"  ✅ {step['name']} completed in {elapsed:.1f}s")
            if result.stdout:
                # Print last 10 lines of output
                lines = result.stdout.strip().split("\n")
                for line in lines[-10:]:
                    print(f"    | {line}")
            return True
        else:
            print(f"  ❌ {step['name']} failed (exit code {result.returncode})")
            if result.stderr:
                for line in result.stderr.strip().split("\n")[-5:]:
                    print(f"    ! {line}")
            return False
    
    except subprocess.TimeoutExpired:
        print(f"  ⏱️  {step['name']} timed out (>1 hour)")
        return False
    except Exception as e:
        print(f"  ❌ Error running {step['name']}: {e}")
        return False


def merge_csvs() -> Any:
    """Merge all processed CSVs into a master dataset."""
    print(f"\n{'═' * 60}")
    print("MERGING ALL DATA SOURCES")
    print(f"{'═' * 60}")
    
    try:
        import pandas as pd  # type: ignore[import-untyped]
    except ImportError:
        print("  ❌ pandas not installed. Run: pip install pandas")
        return None
    
    all_dfs: list[Any] = []
    
    # Scan processed/ for CSV files
    csv_files = list(PROCESSED_DIR.glob("*.csv"))
    
    if not csv_files:
        print("  ⚠️  No CSV files found in processed/")
        return None
    
    print(f"\n  Found {len(csv_files)} CSV files:")
    
    for csv_file in sorted(csv_files):
        if csv_file.name == "master_dataset.csv":
            continue  # Skip our own output
        
        try:
            df: Any = pd.read_csv(csv_file, dtype=str, on_bad_lines='skip')  # type: ignore[reportUnknownMemberType]
            print(f"    {csv_file.name:<40} {len(df):>8,} rows")
            
            # Standardize columns
            df["_source_file"] = csv_file.name
            
            # Try to normalize column names
            col_map: dict[str, str] = {}
            for col in df.columns:
                lower = col.lower().strip()
                if lower in ("name", "business_name", "merchant_name", "itemlabel"):
                    col_map[col] = "name"
                elif lower in ("category", "l1_category", "type"):
                    col_map[col] = "category"
                elif lower in ("subcategory", "l2_category", "subtype"):
                    col_map[col] = "subcategory"
                elif lower in ("city", "district", "location"):
                    col_map[col] = "city"
                elif lower in ("state", "province"):
                    col_map[col] = "state"
                elif lower in ("source",):
                    col_map[col] = "source"
            
            if col_map:
                df = df.rename(columns=col_map)
            
            all_dfs.append(df)
        
        except Exception as e:
            print(f"    ❌ Error reading {csv_file.name}: {e}")
    
    if not all_dfs:
        print("  No valid data to merge")
        return None
    
    # Concatenate all
    master: Any = pd.concat(all_dfs, ignore_index=True, sort=False)
    print(f"\n  📊 Total before dedup: {len(master):,} rows")
    
    # Deduplication strategy
    if "name" in master.columns:
        # Normalize names for dedup
        master["_name_norm"] = (
            master["name"]
            .fillna("")
            .str.lower()
            .str.strip()
            .str.replace(r'[^\w\s]', '', regex=True)
            .str.replace(r'\s+', ' ', regex=True)
        )
        
        # Dedup by normalized name + city (if available)
        dedup_cols = ["_name_norm"]
        if "city" in master.columns:
            master["_city_norm"] = master["city"].fillna("").str.lower().str.strip()
            dedup_cols.append("_city_norm")
        
        before = len(master)
        master = master.drop_duplicates(subset=dedup_cols, keep="first")
        
        # Clean up temp columns
        master = master.drop(columns=[c for c in master.columns if c.startswith("_")], errors='ignore')
        
        print(f"  📊 Total after dedup:  {len(master):,} rows ({before - len(master):,} duplicates removed)")
    
    return master


def generate_stats(master_df: Any) -> dict[str, Any]:
    """Generate statistics summary."""
    stats: dict[str, Any] = {
        "generated_at": datetime.now().isoformat(),
        "total_records": len(master_df),
        "columns": list(master_df.columns),
    }
    
    # Category distribution
    if "category" in master_df.columns:
        cat_counts = master_df["category"].value_counts().to_dict()
        stats["category_distribution"] = {str(k): int(v) for k, v in cat_counts.items()}
    
    # Source distribution
    if "source" in master_df.columns:
        src_counts = master_df["source"].value_counts().to_dict()
        stats["source_distribution"] = {str(k): int(v) for k, v in src_counts.items()}
    
    if "_source_file" in master_df.columns:
        file_counts = master_df["_source_file"].value_counts().to_dict()
        stats["file_distribution"] = {str(k): int(v) for k, v in file_counts.items()}
    
    # City distribution (top 30)
    if "city" in master_df.columns:
        city_counts = master_df["city"].dropna().value_counts().head(30).to_dict()
        stats["top_cities"] = {str(k): int(v) for k, v in city_counts.items()}
    
    # State distribution
    if "state" in master_df.columns:
        state_counts = master_df["state"].dropna().value_counts().to_dict()
        stats["state_distribution"] = {str(k): int(v) for k, v in state_counts.items()}
    
    # Name stats
    if "name" in master_df.columns:
        stats["unique_names"] = int(master_df["name"].nunique())
        stats["null_names"] = int(master_df["name"].isna().sum())
        
        # Average name length
        name_lens = master_df["name"].dropna().str.len()
        stats["avg_name_length"] = round(float(name_lens.mean()), 1)
        stats["max_name_length"] = int(name_lens.max())
    
    return stats


def print_summary(stats: dict[str, Any]) -> None:
    """Print a human-readable summary."""
    print(f"\n{'═' * 60}")
    print("DATASET SUMMARY")
    print(f"{'═' * 60}")
    
    print(f"\n  Total records:   {stats.get('total_records', 0):>10,}")
    print(f"  Unique names:    {stats.get('unique_names', 'N/A'):>10,}")
    print(f"  Columns:         {len(stats.get('columns', []))}")
    
    if "category_distribution" in stats:
        print(f"\n  📊 By Category:")
        for cat, count in sorted(stats["category_distribution"].items(), key=lambda x: -x[1]):
            pct = (count / stats["total_records"]) * 100
            bar = "█" * int(pct / 2)
            print(f"    {cat:<30} {count:>8,} ({pct:5.1f}%) {bar}")
    
    if "source_distribution" in stats:
        print(f"\n  📊 By Source:")
        for src, count in sorted(stats["source_distribution"].items(), key=lambda x: -x[1]):
            print(f"    {src:<30} {count:>8,}")
    
    if "top_cities" in stats:
        print(f"\n  📊 Top 10 Cities:")
        for i, (city, count) in enumerate(list(stats["top_cities"].items())[:10]):
            print(f"    {i+1:>2}. {city:<25} {count:>8,}")


def check_prerequisites() -> list[str]:
    """Check which dependencies are installed."""
    print(f"\n{'═' * 60}")
    print("PREREQUISITE CHECK")
    print(f"{'═' * 60}")
    
    deps: dict[str, str] = {
        "pandas": "Data merging & analysis",
        "requests": "HTTP requests (all scrapers)",
        "tqdm": "Progress bars",
        "osmium": "OSM PBF parsing (script 01)",
        "bs4": "Web scraping (script 03)",
    }
    
    missing: list[str] = []
    
    for module, desc in deps.items():
        try:
            importlib.import_module(module)
            print(f"  ✅ {module:<15} — {desc}")
        except ImportError:
            print(f"  ❌ {module:<15} — {desc}")
            missing.append(module)
    
    # Check API keys
    gmaps_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    print(f"\n  🔑 GOOGLE_MAPS_API_KEY: {'✅ Set' if gmaps_key else '❌ Not set (script 05 will skip)'}")
    
    datagov_key = os.environ.get("DATA_GOV_IN_API_KEY")
    print(f"  🔑 DATA_GOV_IN_API_KEY: {'✅ Set' if datagov_key else '⚠️  Not set (using catalog search)'}")
    
    if missing:
        install_cmd = f"pip install {' '.join(missing)}"
        print(f"\n  To install missing deps: {install_cmd}")
    
    return missing


def main() -> None:
    parser = argparse.ArgumentParser(description="Xpenzo ML Data Collection Pipeline")
    parser.add_argument("--skip-download", action="store_true",
                        help="Skip scripts that require large downloads (OSM, data.gov)")
    parser.add_argument("--only", nargs="+", choices=[s["id"] for s in PIPELINE_STEPS],
                        help="Run only specific scripts")
    parser.add_argument("--merge-only", action="store_true",
                        help="Only merge existing CSVs, don't run any scripts")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be run without executing")
    parser.add_argument("--check", action="store_true",
                        help="Only check prerequisites")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("XPENZO ML DATA COLLECTION PIPELINE")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Ensure output directories exist
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    LABELED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check prerequisites
    _missing: list[str] = check_prerequisites()
    
    if args.check:
        return
    
    # Determine which steps to run
    if args.merge_only:
        steps_to_run: list[dict[str, Any]] = []
    elif args.only:
        steps_to_run = [s for s in PIPELINE_STEPS if s["id"] in args.only]
    elif args.skip_download:
        steps_to_run = [s for s in PIPELINE_STEPS if not s["requires_download"]]
    else:
        steps_to_run = PIPELINE_STEPS
    
    # Sort by priority
    steps_to_run.sort(key=lambda s: s["priority"])
    
    if steps_to_run:
        print(f"\n{'═' * 60}")
        print(f"RUNNING {len(steps_to_run)} PIPELINE STEPS")
        print(f"{'═' * 60}")
        
        results: dict[str, str] = {}
        
        for step in steps_to_run:
            # Skip Google Maps if no API key
            if step["id"] == "google" and not os.environ.get("GOOGLE_MAPS_API_KEY"):
                print(f"\n  ⏭️  Skipping {step['name']} (no API key)")
                results[step["id"]] = "skipped"
                continue
            
            success = run_script(step, dry_run=args.dry_run)
            results[step["id"]] = "success" if success else "failed"
        
        # Print step results
        print(f"\n{'═' * 60}")
        print("STEP RESULTS")
        print(f"{'═' * 60}")
        for step in steps_to_run:
            status = results.get(step["id"], "not_run")
            icon = {"success": "✅", "failed": "❌", "skipped": "⏭️"}.get(status, "❓")
            print(f"  {icon} {step['name']:<30} {status}")
    
    # Merge phase
    if not args.dry_run:
        master_df = merge_csvs()
        
        if master_df is not None and len(master_df) > 0:
            # Save master dataset
            master_path = PROCESSED_DIR / "master_dataset.csv"
            master_df.to_csv(master_path, index=False, encoding='utf-8')  # type: ignore[union-attr]
            print(f"\n  💾 Master dataset: {master_path}")
            
            # Generate and save stats
            stats = generate_stats(master_df)
            stats_path = PROCESSED_DIR / "master_stats.json"
            with open(stats_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            print(f"  💾 Statistics:     {stats_path}")
            
            print_summary(stats)
        else:
            print("\n  ⚠️  No data to merge. Run scripts first!")
    
    print(f"\n{'═' * 60}")
    print(f"Pipeline finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'═' * 60}")
    
    # Print next steps
    print("\n📋 Next Steps:")
    print("  1. Review processed/*.csv files")
    print("  2. Create/verify ml/taxonomy/category_taxonomy.json")
    print("  3. Run labeling pipeline (Copilot Pro + Gemini)")
    print("  4. Train CHT model on Colab/Kaggle")


if __name__ == "__main__":
    main()
