#!/usr/bin/env python3
"""
08_label_dataset.py — Xpenzo Dataset Labeler

Maps 418K+ merchant records from master_dataset.csv to the 520-category
hierarchical taxonomy (15 L1 → 80 L2 → 520 L3).

Labeling Cascade (in priority order):
  1. Brand exact-match   → confidence 0.95
  2. (category, subcategory, osm_tag) rule table → confidence 0.70–0.90
  3. Cuisine → Food L3   → confidence 0.85
  4. Name keyword match   → confidence 0.60–0.80
  5. Fallback "Other"     → confidence 0.30

Output: ml/data_collection/labeled/labeled_dataset.csv
        ml/data_collection/labeled/label_stats.json

Usage:
    python 08_label_dataset.py [--input PATH] [--output-dir PATH]
"""

from __future__ import annotations

import argparse
import csv
import json
import re
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
DEFAULT_INPUT = PROJECT_ROOT / "ml" / "data_collection" / "processed" / "master_dataset.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "ml" / "data_collection" / "labeled"


# ═══════════════════════════════════════════════════════════════════════════
# TAXONOMY LOADER
# ═══════════════════════════════════════════════════════════════════════════

class Taxonomy:
    """Loads the 520-category taxonomy and builds fast lookup indexes."""

    def __init__(self, path: str | Path) -> None:
        with open(path, "r", encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)

        cats: list[dict[str, Any]] = data["categories"]

        # L3 code → full info dict
        self.l3_by_code: dict[str, dict[str, Any]] = {}
        # L3 id → full info dict
        self.l3_by_id: dict[int, dict[str, Any]] = {}
        # L2 code → L2 info + parent L1 info
        self.l2_by_code: dict[str, dict[str, Any]] = {}
        # L1 code → L1 info
        self.l1_by_code: dict[str, dict[str, Any]] = {}
        # brand (lowercase) → L3 code
        self.brand_to_l3: dict[str, str] = {}
        # keyword (lowercase) → list of (l3_code, keyword_length) for scoring
        self.keyword_to_l3: dict[str, list[tuple[str, int]]] = {}

        for l1 in cats:
            l1_info: dict[str, Any] = {
                "l1_id": l1["l1_id"],
                "l1_code": l1["l1_code"],
                "l1_name": l1["l1_name"],
            }
            self.l1_by_code[l1["l1_code"]] = l1_info

            for l2 in l1["subcategories"]:
                l2_info: dict[str, Any] = {
                    "l2_id": l2["l2_id"],
                    "l2_code": l2["l2_code"],
                    "l2_name": l2["l2_name"],
                    **l1_info,
                }
                self.l2_by_code[l2["l2_code"]] = l2_info

                for l3 in l2["micro_categories"]:
                    l3_info: dict[str, Any] = {
                        "l3_id": l3["l3_id"],
                        "l3_code": l3["l3_code"],
                        "l3_name": l3["l3_name"],
                        **l2_info,
                    }
                    self.l3_by_code[l3["l3_code"]] = l3_info
                    self.l3_by_id[l3["l3_id"]] = l3_info

                    # Index example_merchants as brands
                    merchants: list[str] = l3.get("example_merchants", [])
                    for m in merchants:
                        self.brand_to_l3[m.lower().strip()] = l3["l3_code"]

                    # Index keywords
                    keywords: list[str] = l3.get("keywords", [])
                    for kw in keywords:
                        kw_lower = kw.lower().strip()
                        if kw_lower not in self.keyword_to_l3:
                            self.keyword_to_l3[kw_lower] = []
                        self.keyword_to_l3[kw_lower].append(
                            (l3["l3_code"], len(kw_lower))
                        )

    def get_l3(self, code: str) -> dict[str, Any] | None:
        return self.l3_by_code.get(code)

    def get_l3_info(self, code: str) -> dict[str, Any]:
        """Return full hierarchy info for an L3 code, or empty dict."""
        return self.l3_by_code.get(code, {})

    def find_other_code(self, l2_code: str) -> str | None:
        """Find the *_OTH L3 code under a given L2."""
        for code in self.l3_by_code:
            if code.startswith(l2_code) and code.endswith("_OTH"):
                return code
        return None


# ═══════════════════════════════════════════════════════════════════════════
# LABEL RESULT
# ═══════════════════════════════════════════════════════════════════════════

class LabelResult:
    """Wraps an assigned label with confidence + method."""

    __slots__ = ("l3_code", "confidence", "method")

    def __init__(self, l3_code: str, confidence: float, method: str) -> None:
        self.l3_code = l3_code
        self.confidence = confidence
        self.method = method


# ═══════════════════════════════════════════════════════════════════════════
# LAYER 1: BRAND EXACT MATCH
# ═══════════════════════════════════════════════════════════════════════════

def match_brand(row: dict[str, str], tax: Taxonomy) -> LabelResult | None:
    """Check if `brand` OR `name` is a known merchant → L3 (confidence 0.95)."""
    brand = row.get("brand", "").strip().lower()
    if brand and brand in tax.brand_to_l3:
        return LabelResult(tax.brand_to_l3[brand], 0.95, "brand_exact")

    # Also try name as brand (catches cases like "McDonald's" in name field)
    name = row.get("name", "").strip().lower()
    if name and name in tax.brand_to_l3:
        return LabelResult(tax.brand_to_l3[name], 0.93, "name_as_brand")

    # Fuzzy brand: check if any known brand is a substring of name
    if name:
        for b, code in tax.brand_to_l3.items():
            if len(b) >= 4 and b in name:
                return LabelResult(code, 0.88, "brand_substring")

    return None


# ═══════════════════════════════════════════════════════════════════════════
# LAYER 2: (CATEGORY, SUBCATEGORY) RULE TABLE
# ═══════════════════════════════════════════════════════════════════════════

# Maps (source_category, source_subcategory) → L3 code
# Covers the top ~200 pairs that account for >95% of records.
# Format: (category_lower, subcategory_lower) → l3_code

SUBCATEGORY_RULES: dict[tuple[str, str], str] = {
    # ── HEALTHCARE ────────────────────────────────────────────────────
    ("healthcare", "hospital"): "HC_HOSP_MS",
    ("healthcare", "hospitals"): "HC_HOSP_MS",
    ("healthcare", "centre"): "HC_HOSP_MS",
    ("healthcare", "clinic"): "HC_HOSP_PC",
    ("healthcare", "dentist"): "HC_DNTL_DC",
    ("healthcare", "pharmacy"): "HC_PHRM_RT",
    ("healthcare", "doctor"): "HC_DCTR_GP",
    ("healthcare", "doctors"): "HC_DCTR_GP",
    ("healthcare", "alternative"): "HC_PHRM_AY",
    ("healthcare", "veterinary"): "HC_DCTR_OTH",
    ("healthcare", "laboratory"): "HC_DIAG_PL",
    ("healthcare", "physiotherapist"): "HC_DCTR_SP",
    ("healthcare", "blood donation"): "HC_HOSP_OTH",
    ("healthcare", "optometrist"): "HC_DNTL_OP",
    ("healthcare", "midwife"): "HC_HOSP_MT",
    ("healthcare", "counselling"): "HC_DCTR_PS",
    ("healthcare", "psychotherapist"): "HC_DCTR_PS",
    ("healthcare", "community health center"): "HC_HOSP_GV",
    ("healthcare", "medical laboratory"): "HC_DIAG_PL",
    ("healthcare", "yes"): "HC_HOSP_OTH",
    ("healthcare", "social facility"): "HC_HOSP_OTH",
    ("healthcare", "nursing home"): "HC_HOSP_NH",

    # ── SHOPPING ──────────────────────────────────────────────────────
    ("shopping", "clothing"): "SH_CLTH_OTH",
    ("shopping", "clothes"): "SH_CLTH_OTH",
    ("shopping", "supermarket"): "FD_GROC_SM",
    ("shopping", "supermarkets"): "FD_GROC_SM",
    ("shopping", "convenience store"): "SH_GENR_OTH",
    ("shopping", "convenience"): "SH_GENR_OTH",
    ("shopping", "general store"): "FD_GROC_KR",
    ("shopping", "general"): "FD_GROC_KR",
    ("shopping", "grocery"): "FD_GROC_KR",
    ("shopping", "books & stationery"): "SH_BOOK_PB",
    ("shopping", "stationery"): "SH_BOOK_ST",
    ("shopping", "jewellery"): "SH_JWLR_GL",
    ("shopping", "jewelry"): "SH_JWLR_GL",
    ("shopping", "hardware"): "SH_GENR_HW",
    ("shopping", "electronics"): "SH_ELEC_OTH",
    ("shopping", "mobile & accessories"): "SH_ELEC_MP",
    ("shopping", "mobile_phone"): "SH_ELEC_MP",
    ("shopping", "mall"): "SH_GENR_ML",
    ("shopping", "furniture"): "SH_HOME_FN",
    ("shopping", "medical supply"): "HC_PHRM_ME",
    ("shopping", "footwear"): "SH_CLTH_FW",
    ("shopping", "shoes"): "SH_CLTH_FW",
    ("shopping", "department store"): "SH_GENR_DS",
    ("shopping", "confectionery"): "FD_BAKE_MT",
    ("shopping", "electrical"): "SH_ELEC_OTH",
    ("shopping", "meat & poultry"): "FD_GROC_MF",
    ("shopping", "dairy"): "FD_GROC_DR",
    ("shopping", "eyewear"): "HC_DNTL_OP",
    ("shopping", "gifts"): "SH_GENR_GF",
    ("shopping", "tyres"): "TR_MAINT_TY",
    ("shopping", "tea"): "FD_GROC_OTH",
    ("shopping", "car parts"): "TR_MAINT_SP",
    ("shopping", "chemist"): "HC_PHRM_RT",
    ("shopping", "alcohol"): "FD_ALCL_WS",
    ("shopping", "sports equipment"): "SH_GENR_SP",
    ("shopping", "pet supplies"): "FS_PET_AC",
    ("shopping", "photo"): "EN_HBBY_PH",
    ("shopping", "interior decoration"): "SH_HOME_DC",
    ("shopping", "paint"): "SH_GENR_HW",
    ("shopping", "beverages"): "FD_GROC_OTH",
    ("shopping", "cosmetics"): "PC_BEAU_MK",
    ("shopping", "variety store"): "SH_GENR_OTH",
    ("shopping", "bicycle"): "TR_MAINT_OTH",
    ("shopping", "garden centre"): "EN_HBBY_GD",
    ("shopping", "toys"): "SH_GENR_TY",
    ("shopping", "trade"): "SH_GENR_OTH",
    ("shopping", "outdoor"): "SH_GENR_SP",
    ("shopping", "fabric"): "SH_CLTH_OTH",
    ("shopping", "ticket"): "EN_EVNT_OTH",
    ("shopping", "travel agency"): "TV_TOUR_PK",
    ("shopping", "yes"): "SH_GENR_OTH",
    ("shopping", "motorcycle repair"): "TR_MAINT_TW",
    ("shopping", "hifi"): "SH_ELEC_AU",
    ("shopping", "music"): "SH_GENR_MS",
    ("shopping", "video"): "SH_ELEC_OTH",
    ("shopping", "video games"): "EN_GAME_PC",
    ("shopping", "nutrition supplements"): "PC_WELL_VS",
    ("shopping", "frozen food"): "FD_GROC_FZ",
    ("shopping", "country store"): "SH_GENR_OTH",
    ("shopping", "antiques"): "SH_GENR_OTH",
    ("shopping", "fashion"): "SH_CLTH_OTH",
    ("shopping", "camera"): "SH_ELEC_CM",
    ("shopping", "newsagent"): "SH_BOOK_NP",
    ("shopping", "printing"): "PS_FRLC_PD",
    ("shopping", "pawnbroker"): "FI_BANK_OTH",
    ("shopping", "motorcycle parts"): "TR_MAINT_SP",
    ("shopping", "sewing"): "SH_CLTH_OTH",
    ("shopping", "hearing aids"): "HC_PHRM_ME",
    ("shopping", "pottery"): "EN_HBBY_CR",
    ("shopping", "chocolate"): "FD_BAKE_CH",
    ("shopping", "rice"): "FD_GROC_GR",
    ("shopping", "nuts"): "FD_GROC_DF",
    ("shopping", "deli"): "FD_GROC_OTH",
    ("shopping", "party"): "FS_GIFT_OTH",
    ("shopping", "perfumery"): "PC_BEAU_PF",
    ("shopping", "water"): "UT_WATR_OTH",
    ("shopping", "flooring"): "SH_HOME_OTH",
    ("shopping", "carpet"): "SH_HOME_OTH",
    ("shopping", "doors"): "SH_HOME_OTH",
    ("shopping", "frame"): "SH_HOME_DC",
    ("shopping", "leather"): "SH_CLTH_AC",
    ("shopping", "building materials"): "SH_GENR_HW",
    ("shopping", "food"): "FD_GROC_OTH",
    ("shopping", "funeral directors"): "FS_RELG_OTH",
    ("shopping", "mobile phone accessories"): "SH_ELEC_MP",
    ("shopping", "rental"): "SH_GENR_OTH",
    ("shopping", "curtain"): "SH_HOME_DC",
    ("shopping", "money lender"): "FI_LOAN_OTH",
    ("shopping", "herbalist"): "HC_PHRM_AY",
    ("shopping", "storage rental"): "PS_COUR_WH",
    ("shopping", "tool hire"): "SH_GENR_HW",
    ("shopping", "pyrotechnics"): "FS_GIFT_FT",
    ("shopping", "telecommunication"): "TC_MOB_OTH",
    ("shopping", "e-cigarette"): "SH_GENR_OTH",
    ("shopping", "printer ink"): "SH_BOOK_ST",
    ("shopping", "bookmaker"): "SH_BOOK_PB",
    ("shopping", "radiotechnics"): "SH_ELEC_OTH",
    ("shopping", "online service"): "SH_ONLN_OTH",
    ("shopping", "market place"): "SH_GENR_WM",

    # ── FOOD & DINING ─────────────────────────────────────────────────
    ("food & dining", "restaurant"): "FD_REST_OTH",
    ("food & dining", "restaurants"): "FD_REST_OTH",
    ("food & dining", "cafe"): "FD_CAFE_OTH",
    ("food & dining", "fast food"): "FD_FAST_OTH",
    ("food & dining", "fast_food"): "FD_FAST_OTH",
    ("food & dining", "bakery"): "FD_BAKE_OTH",
    ("food & dining", "bar"): "FD_ALCL_BP",
    ("food & dining", "food court"): "FD_FAST_QS",
    ("food & dining", "desserts"): "FD_BAKE_CK",
    ("food & dining", "ice cream"): "FD_BAKE_IP",
    ("food & dining", "pub"): "FD_ALCL_BP",
    ("food & dining", "biergarten"): "FD_ALCL_MB",
    ("food & dining", "food"): "FD_REST_OTH",

    # ── EDUCATION ─────────────────────────────────────────────────────
    ("education", "school"): "ED_SCHL_OTH",
    ("education", "college"): "ED_HIGH_CF",
    ("education", "educational institution"): "ED_COACH_OTH",
    ("education", "education"): "ED_SCHL_OTH",
    ("education", "pre-school"): "FS_BABY_DC",
    ("education", "kindergarten"): "FS_BABY_DC",
    ("education", "university"): "ED_HIGH_CF",
    ("education", "institute"): "ED_COACH_OTH",
    ("education", "academy"): "ED_COACH_OTH",
    ("education", "library"): "SH_BOOK_PB",
    ("education", "training"): "ED_COACH_OTH",
    ("education", "driving school"): "GV_FEES_DL",
    ("education", "diving school"): "EN_SPRT_OTH",
    ("education", "research institute"): "ED_HIGH_OTH",
    ("education", "language school"): "ED_COACH_LN",
    ("education", "music school"): "ED_COACH_MA",
    ("education", "dance school"): "ED_COACH_MA",

    # ── RELIGIOUS ─────────────────────────────────────────────────────
    ("religious", "temple/mosque/church"): "FS_RELG_TV",
    ("religious", "place_of_worship"): "FS_RELG_TV",

    # ── BUSINESS & OFFICE ─────────────────────────────────────────────
    ("business & office", "government"): "GV_DGOV_OTH",
    ("business & office", "educational institution"): "ED_COACH_OTH",
    ("business & office", "company"): "PS_FNSV_OTH",
    ("business & office", "yes"): "PS_FNSV_OTH",
    ("business & office", "it"): "PS_FRLC_SS",
    ("business & office", "financial"): "PS_FNSV_FA",
    ("business & office", "estate agent"): "UT_RENT_BK",
    ("business & office", "telecommunication"): "TC_LAND_OTH",
    ("business & office", "lawyer"): "PS_LEGL_LF",
    ("business & office", "ngo"): "FS_DONA_NG",
    ("business & office", "accountant"): "PS_FNSV_CA",
    ("business & office", "architect"): "PS_FNSV_OTH",
    ("business & office", "insurance"): "FI_INSR_OTH",
    ("business & office", "newspaper"): "SH_BOOK_NP",
    ("business & office", "advertising"): "PS_FRLC_DM",
    ("business & office", "consulting"): "PS_FNSV_OTH",
    ("business & office", "association"): "PS_FNSV_OTH",
    ("business & office", "logistics"): "PS_COUR_OTH",
    ("business & office", "charity"): "FS_DONA_NG",
    ("business & office", "courier"): "PS_COUR_DM",
    ("business & office", "security"): "PS_FNSV_OTH",
    ("business & office", "guide"): "TV_TOUR_OTH",
    ("business & office", "foundation"): "FS_DONA_NG",
    ("business & office", "financial advisor"): "PS_FNSV_FA",
    ("business & office", "engineer"): "PS_FNSV_OTH",
    ("business & office", "tax advisor"): "PS_FNSV_TC",
    ("business & office", "graphic design"): "PS_FRLC_PD",
    ("business & office", "cooperative"): "PS_FNSV_OTH",
    ("business & office", "water utility"): "UT_WATR_WB",
    ("business & office", "employment agency"): "PS_FNSV_OTH",
    ("business & office", "property management"): "UT_RENT_BK",
    ("business & office", "moving company"): "PS_COUR_PM",
    ("business & office", "construction company"): "PS_FNSV_OTH",
    ("business & office", "administrative"): "GV_DGOV_OTH",
    ("business & office", "union"): "PS_FNSV_OTH",
    ("business & office", "political party"): "GV_DGOV_OTH",
    ("business & office", "digital marketing"): "PS_FRLC_DM",
    ("business & office", "media"): "PS_FRLC_DM",
    ("business & office", "web hosting & app development services"): "PS_FRLC_DH",

    # ── BUSINESS ──────────────────────────────────────────────────────
    ("business", "companies"): "PS_FNSV_OTH",

    # ── TRAVEL & ACCOMMODATION ────────────────────────────────────────
    ("travel & accommodation", "hotel"): "TV_HOTL_OTH",
    ("travel & accommodation", "hotels"): "TV_HOTL_OTH",
    ("travel & accommodation", "guest house"): "TV_HOTL_HM",
    ("travel & accommodation", "hostel"): "TV_HOTL_HS",
    ("travel & accommodation", "camping"): "TV_TOUR_AD",
    ("travel & accommodation", "motel"): "TV_HOTL_OTH",
    ("travel & accommodation", "camp site"): "TV_TOUR_AD",
    ("travel & accommodation", "resort"): "TV_HOTL_RS",
    ("travel & accommodation", "caravan site"): "TV_TOUR_AD",
    ("travel & accommodation", "chalet"): "TV_HOTL_HM",
    ("travel & accommodation", "alpine hut"): "TV_HOTL_HM",
    ("travel & accommodation", "wilderness hut"): "TV_HOTL_HM",
    ("travel & accommodation", "apartment"): "TV_HOTL_HM",
    ("travel & accommodation", "lodge"): "TV_HOTL_BG",

    # ── SERVICES ──────────────────────────────────────────────────────
    ("services", "post office"): "PS_COUR_SP",
    ("services", "salon"): "PC_SALN_UX",
    ("services", "hairdresser"): "PC_SALN_UX",
    ("services", "beauty parlour"): "PC_SALN_WS",
    ("services", "beauty"): "PC_SALN_WS",
    ("services", "tailor"): "SH_CLTH_OTH",
    ("services", "computer repair"): "SH_ELEC_OTH",
    ("services", "printing"): "PS_FRLC_PD",
    ("services", "electronics repair"): "SH_ELEC_OTH",
    ("services", "laundry"): "UT_CLEN_LN",
    ("services", "dry cleaning"): "UT_CLEN_DC",
    ("services", "locksmith"): "UT_HSVC_OTH",
    ("services", "car repair"): "TR_MAINT_CS",
    ("services", "painter"): "UT_HSVC_OTH",
    ("services", "copyshop"): "PS_FRLC_PD",
    ("services", "pest control"): "UT_HSVC_PC",
    ("services", "money transfer"): "FI_BANK_FT",
    ("services", "travel agent"): "TV_TOUR_PK",
    ("services", "funeral"): "FS_RELG_OTH",
    ("services", "cobbler"): "SH_CLTH_FW",
    ("services", "plumber"): "UT_HSVC_PL",
    ("services", "electrician"): "UT_HSVC_EL",
    ("services", "carpenter"): "UT_HSVC_CP",
    ("services", "hvac"): "UT_HSVC_OTH",
    ("services", "grinding mill"): "SH_GENR_OTH",
    ("services", "dressmaker"): "SH_CLTH_OTH",
    ("services", "photo studio"): "EN_HBBY_PH",
    ("services", "cleaning"): "UT_CLEN_HC",
    ("services", "key cutter"): "UT_HSVC_OTH",
    ("services", "gardener"): "EN_HBBY_GD",
    ("services", "shoemaker"): "SH_CLTH_FW",
    ("services", "tiler"): "UT_HSVC_OTH",
    ("services", "glaziery"): "UT_HSVC_OTH",
    ("services", "watchmaker"): "SH_JWLR_WT",
    ("services", "stonemason"): "UT_HSVC_OTH",
    ("services", "agricultural engines"): "SH_GENR_OTH",
    ("services", "bookbinder"): "SH_BOOK_OTH",
    ("services", "signmaker"): "PS_FRLC_PD",
    ("services", "upholsterer"): "SH_HOME_FN",
    ("services", "winery"): "FD_ALCL_OTH",
    ("services", "print shop"): "PS_FRLC_PD",
    ("services", "jeweller"): "SH_JWLR_GL",
    ("services", "builder"): "PS_FNSV_OTH",
    ("services", "yes"): "PS_FNSV_OTH",
    ("services", "packing material"): "PS_COUR_OTH",
    ("services", "window construction"): "UT_HSVC_OTH",
    ("services", "photographic laboratory"): "EN_HBBY_PH",

    # ── TRANSPORTATION ────────────────────────────────────────────────
    ("transportation", "fuel station"): "TR_FUEL_PT",
    ("transportation", "fuel"): "TR_FUEL_PT",
    ("transportation", "car service"): "TR_MAINT_CS",
    ("transportation", "car repair"): "TR_MAINT_CS",
    ("transportation", "car dealer"): "TR_MAINT_OTH",
    ("transportation", "car"): "TR_MAINT_OTH",
    ("transportation", "two-wheeler dealer"): "TR_MAINT_TW",
    ("transportation", "motorcycle"): "TR_MAINT_TW",
    ("transportation", "parking"): "TR_PARK_LT",
    ("transportation", "car wash"): "TR_MAINT_CW",
    ("transportation", "bicycle shop"): "TR_MAINT_OTH",
    ("transportation", "bicycle"): "TR_MAINT_OTH",
    ("transportation", "transport"): "PS_COUR_OTH",
    ("transportation", "boat"): "TV_TOUR_CR",
    ("transportation", "bus"): "TR_PUB_CB",
    ("transportation", "taxi"): "TR_RIDE_OTH",
    ("transportation", "car rental"): "TV_CAB_SD",
    ("transportation", "bus station"): "TR_PUB_SB",

    # ── FINANCE ───────────────────────────────────────────────────────
    ("finance", "bank"): "FI_BANK_OTH",
    ("finance", "banks"): "FI_BANK_OTH",
    ("finance", "atm"): "MS_CASH_AW",
    ("finance", "money transfer"): "FI_BANK_FT",
    ("finance", "bureau de change"): "MS_CASH_FX",
    ("finance", "credit union"): "FI_BANK_OTH",
    ("finance", "microfinance"): "FI_LOAN_OTH",

    # ── ENTERTAINMENT ─────────────────────────────────────────────────
    ("entertainment", "cinema"): "EN_MOVR_MP",
    ("entertainment", "theatre"): "EN_EVNT_OTH",
    ("entertainment", "museum"): "TV_TOUR_SS",
    ("entertainment", "community centre"): "EN_EVNT_OTH",
    ("entertainment", "nightclub"): "FD_ALCL_LG",
    ("entertainment", "arts centre"): "EN_HBBY_CR",
    ("entertainment", "events venue"): "EN_EVNT_OTH",
    ("entertainment", "gambling"): "EN_GAME_OTH",
    ("entertainment", "amusement arcade"): "EN_EVNT_TP",
    ("entertainment", "water park"): "EN_EVNT_TP",
    ("entertainment", "theme park"): "EN_EVNT_TP",
    ("entertainment", "zoo"): "TV_TOUR_WL",
    ("entertainment", "studio"): "EN_HBBY_PH",
    ("entertainment", "miniature golf"): "EN_SPRT_OTH",
    ("entertainment", "bowling alley"): "EN_SPRT_OTH",
    ("entertainment", "escape game"): "EN_EVNT_VR",
    ("entertainment", "planetarium"): "TV_TOUR_SS",
    ("entertainment", "aquarium"): "TV_TOUR_WL",

    # ── FITNESS & WELLNESS ────────────────────────────────────────────
    ("fitness & wellness", "gym"): "PC_FIT_GM",
    ("fitness & wellness", "fitness_centre"): "PC_FIT_GM",
    ("fitness & wellness", "sports complex"): "EN_SPRT_AC",
    ("fitness & wellness", "swimming pool"): "EN_SPRT_SW",
    ("fitness & wellness", "sports centre"): "EN_SPRT_AC",
    ("fitness & wellness", "yoga"): "PC_FIT_YG",
    ("fitness & wellness", "sauna"): "PC_SPA_SS",

    # ── TELECOM ───────────────────────────────────────────────────────
    ("telecom", "telecom"): "TC_MOB_OTH",
}


# ── OSM TAG overrides (when subcategory alone is ambiguous) ──────────────
OSM_TAG_OVERRIDES: dict[str, str] = {
    "pharmacy": "HC_PHRM_RT",
    "hospital": "HC_HOSP_MS",
    "clinic": "HC_HOSP_PC",
    "dentist": "HC_DNTL_DC",
    "doctors": "HC_DCTR_GP",
    "veterinary": "HC_DCTR_OTH",
    "optician": "HC_DNTL_OP",
    "bank": "FI_BANK_OTH",
    "atm": "MS_CASH_AW",
    "post_office": "PS_COUR_SP",
    "police": "GV_DGOV_OTH",
    "fire_station": "GV_DGOV_OTH",
    "fuel": "TR_FUEL_PT",
    "car_repair": "TR_MAINT_CS",
    "car_wash": "TR_MAINT_CW",
    "car": "TR_MAINT_OTH",
    "motorcycle": "TR_MAINT_TW",
    "bicycle": "TR_MAINT_OTH",
    "parking": "TR_PARK_LT",
    "taxi": "TR_RIDE_OTH",
    "bus_station": "TR_PUB_SB",
    "restaurant": "FD_REST_OTH",
    "fast_food": "FD_FAST_OTH",
    "cafe": "FD_CAFE_OTH",
    "bar": "FD_ALCL_BP",
    "pub": "FD_ALCL_BP",
    "biergarten": "FD_ALCL_MB",
    "ice_cream": "FD_BAKE_IP",
    "bakery": "FD_BAKE_OTH",
    "cinema": "EN_MOVR_MP",
    "theatre": "EN_EVNT_OTH",
    "nightclub": "FD_ALCL_LG",
    "school": "ED_SCHL_OTH",
    "college": "ED_HIGH_CF",
    "university": "ED_HIGH_CF",
    "kindergarten": "FS_BABY_DC",
    "library": "SH_BOOK_PB",
    "place_of_worship": "FS_RELG_TV",
    "hotel": "TV_HOTL_OTH",
    "hostel": "TV_HOTL_HS",
    "guest_house": "TV_HOTL_HM",
    "camp_site": "TV_TOUR_AD",
    "fitness_centre": "PC_FIT_GM",
    "swimming_pool": "EN_SPRT_SW",
    "clothes": "SH_CLTH_OTH",
    "shoes": "SH_CLTH_FW",
    "jewelry": "SH_JWLR_GL",
    "supermarket": "FD_GROC_SM",
    "convenience": "SH_GENR_OTH",
    "electronics": "SH_ELEC_OTH",
    "hardware": "SH_GENR_HW",
    "furniture": "SH_HOME_FN",
    "mobile_phone": "SH_ELEC_MP",
    "beauty": "PC_SALN_WS",
    "hairdresser": "PC_SALN_UX",
    "laundry": "UT_CLEN_LN",
    "dry_cleaning": "UT_CLEN_DC",
    "tailor": "SH_CLTH_OTH",
    "mall": "SH_GENR_ML",
    "stationery": "SH_BOOK_ST",
    "general": "FD_GROC_KR",
    "grocery": "FD_GROC_KR",
    "medical_supply": "HC_PHRM_ME",
    "company": "PS_FNSV_OTH",
    "government": "GV_DGOV_OTH",
    "educational_institution": "ED_COACH_OTH",
    "yes": "MS_UNKN_UD",
    "centre": "HC_HOSP_MS",
    "museum": "TV_TOUR_SS",
    "arts_centre": "EN_HBBY_CR",
    "community_centre": "EN_EVNT_OTH",
    "water_park": "EN_EVNT_TP",
}


def match_rules(row: dict[str, str], tax: Taxonomy) -> LabelResult | None:
    """Use (category, subcategory) rule table, fallback to osm_tag override."""
    cat = row.get("category", "").strip().lower()
    sub = row.get("subcategory", "").strip().lower()
    osm = row.get("osm_tag", "").strip().lower()

    # Try exact (category, subcategory) match
    key = (cat, sub)
    if key in SUBCATEGORY_RULES:
        code = SUBCATEGORY_RULES[key]
        if code in tax.l3_by_code:
            return LabelResult(code, 0.85, "rule_cat_sub")

    # Try OSM tag override
    if osm and osm in OSM_TAG_OVERRIDES:
        code = OSM_TAG_OVERRIDES[osm]
        if code in tax.l3_by_code:
            return LabelResult(code, 0.80, "rule_osm_tag")

    # Try (category, osm_tag) as subcategory proxy
    key2 = (cat, osm)
    if key2 in SUBCATEGORY_RULES:
        code = SUBCATEGORY_RULES[key2]
        if code in tax.l3_by_code:
            return LabelResult(code, 0.78, "rule_cat_osm")

    return None


# ═══════════════════════════════════════════════════════════════════════════
# LAYER 3: CUISINE → FOOD L3
# ═══════════════════════════════════════════════════════════════════════════

CUISINE_MAP: dict[str, str] = {
    # Indian regional
    "indian": "FD_REST_OTH",
    "north_indian": "FD_REST_NI",
    "north indian": "FD_REST_NI",
    "punjabi": "FD_REST_NI",
    "south_indian": "FD_REST_SI",
    "south indian": "FD_REST_SI",
    "dosa": "FD_REST_SI",
    "idli": "FD_REST_SI",
    "chinese": "FD_REST_CH",
    "indo-chinese": "FD_REST_CH",
    "italian": "FD_REST_IT",
    "pizza": "FD_FAST_PZ",
    "japanese": "FD_REST_JK",
    "korean": "FD_REST_JK",
    "thai": "FD_REST_JK",
    "mughlai": "FD_REST_MG",
    "biryani": "FD_REST_MG",
    "kebab": "FD_REST_MG",
    "bengali": "FD_REST_BN",
    "gujarati": "FD_REST_GJ",
    "rajasthani": "FD_REST_GJ",
    "kerala": "FD_REST_KR",
    "continental": "FD_REST_CT",
    "french": "FD_REST_CT",
    "multi-cuisine": "FD_REST_MC",
    "multicuisine": "FD_REST_MC",
    "burger": "FD_FAST_BG",
    "sandwich": "FD_FAST_SW",
    "ice_cream": "FD_BAKE_IP",
    "ice cream": "FD_BAKE_IP",
    "coffee": "FD_CAFE_CC",
    "tea": "FD_CAFE_TH",
    "juice": "FD_CAFE_JC",
    "bakery": "FD_BAKE_OTH",
    "cake": "FD_BAKE_CK",
    "sweets": "FD_BAKE_MT",
    "dessert": "FD_BAKE_CK",
    "seafood": "FD_REST_KR",
    "vegetarian": "FD_REST_OTH",
    "vegan": "FD_REST_OTH",
    "mexican": "FD_REST_OTH",
    "american": "FD_FAST_BG",
    "asian": "FD_REST_JK",
    "mediterranean": "FD_REST_CT",
    "regional": "FD_REST_OTH",
    "steak": "FD_REST_CT",
    "sushi": "FD_REST_JK",
    "noodles": "FD_REST_CH",
    "chicken": "FD_FAST_FC",
    "fish": "FD_REST_KR",
    "momos": "FD_FAST_MO",
    "chaat": "FD_STRT_CT",
    "pav_bhaji": "FD_FAST_PB",
    "shawarma": "FD_FAST_WR",
    "roll": "FD_FAST_WR",
}


def match_cuisine(row: dict[str, str], tax: Taxonomy) -> LabelResult | None:
    """Map cuisine field to food L3 category."""
    cuisine_raw = row.get("cuisine", "").strip().lower()
    if not cuisine_raw:
        return None

    # Cuisine can be semicolon-separated; take first match
    for part in re.split(r"[;,|]", cuisine_raw):
        c = part.strip().replace(" ", "_") if "_" not in part.strip() else part.strip()
        c_nounderscore = c.replace("_", " ")

        if c in CUISINE_MAP:
            code = CUISINE_MAP[c]
            if code in tax.l3_by_code:
                return LabelResult(code, 0.85, "cuisine_map")
        if c_nounderscore in CUISINE_MAP:
            code = CUISINE_MAP[c_nounderscore]
            if code in tax.l3_by_code:
                return LabelResult(code, 0.85, "cuisine_map")

    return None


# ═══════════════════════════════════════════════════════════════════════════
# LAYER 4: NAME KEYWORD MATCH
# ═══════════════════════════════════════════════════════════════════════════

def match_name_keywords(
    row: dict[str, str], tax: Taxonomy
) -> LabelResult | None:
    """Match business name against taxonomy keywords. Longer match wins."""
    name = row.get("name", "").strip().lower()
    if not name or len(name) < 3:
        return None

    best_code: str | None = None
    best_len: int = 0

    for kw, entries in tax.keyword_to_l3.items():
        if len(kw) < 3:
            continue
        if kw in name:
            for code, kw_len in entries:
                if kw_len > best_len:
                    best_code = code
                    best_len = kw_len

    if best_code and best_len >= 4:
        conf = min(0.80, 0.55 + best_len * 0.03)
        return LabelResult(best_code, conf, "name_keyword")

    return None


# ═══════════════════════════════════════════════════════════════════════════
# LAYER 5: CATEGORY-LEVEL FALLBACK
# ═══════════════════════════════════════════════════════════════════════════

# Source category → L1 "Other" L3 code
CATEGORY_FALLBACK: dict[str, str] = {
    "healthcare": "HC_HOSP_OTH",
    "shopping": "SH_GENR_OTH",
    "food & dining": "FD_REST_OTH",
    "education": "ED_SCHL_OTH",
    "religious": "FS_RELG_OTH",
    "business & office": "PS_FNSV_OTH",
    "business": "PS_FNSV_OTH",
    "travel & accommodation": "TV_HOTL_OTH",
    "services": "UT_HSVC_OTH",
    "transportation": "TR_MAINT_OTH",
    "finance": "FI_BANK_OTH",
    "entertainment": "EN_EVNT_OTH",
    "fitness & wellness": "PC_FIT_OTH",
    "telecom": "TC_MOB_OTH",
}


def match_fallback(row: dict[str, str], tax: Taxonomy) -> LabelResult:
    """Last resort: map source category → 'Other' L3 in the closest L1."""
    cat = row.get("category", "").strip().lower()
    code = CATEGORY_FALLBACK.get(cat, "MS_UNKN_OTH")
    if code not in tax.l3_by_code:
        code = "MS_UNKN_OTH"
    return LabelResult(code, 0.30, "fallback_category")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN LABELING ENGINE
# ═══════════════════════════════════════════════════════════════════════════

def label_record(row: dict[str, str], tax: Taxonomy) -> LabelResult:
    """Run the 5-layer cascade and return the first match."""
    # Layer 1: Brand exact match
    result = match_brand(row, tax)
    if result:
        return result

    # Layer 2: Rule table (category, subcategory, osm_tag)
    result = match_rules(row, tax)
    if result:
        return result

    # Layer 3: Cuisine → Food L3
    result = match_cuisine(row, tax)
    if result:
        return result

    # Layer 4: Name keyword match
    result = match_name_keywords(row, tax)
    if result:
        return result

    # Layer 5: Fallback
    return match_fallback(row, tax)


# ═══════════════════════════════════════════════════════════════════════════
# OUTPUT / STATS
# ═══════════════════════════════════════════════════════════════════════════

OUTPUT_FIELDS: list[str] = [
    # Original key columns
    "name", "brand", "category", "subcategory", "osm_tag", "cuisine",
    "city", "state", "lat", "lon", "phone", "website",
    # New label columns
    "l1_id", "l1_code", "l1_name",
    "l2_id", "l2_code", "l2_name",
    "l3_id", "l3_code", "l3_name",
    "confidence", "match_method",
]


def build_output_row(
    row: dict[str, str], label: LabelResult, tax: Taxonomy
) -> dict[str, Any]:
    """Merge original row fields with label columns."""
    info = tax.get_l3_info(label.l3_code)
    out: dict[str, Any] = {}
    for field in OUTPUT_FIELDS:
        if field in info:
            out[field] = info[field]
        elif field == "confidence":
            out[field] = round(label.confidence, 2)
        elif field == "match_method":
            out[field] = label.method
        else:
            out[field] = row.get(field, "")
    return out


def compute_stats(
    labeled_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute labeling statistics."""
    total = len(labeled_rows)

    method_counts: dict[str, int] = defaultdict(int)
    confidence_buckets: dict[str, int] = {
        "0.90-1.00": 0,
        "0.80-0.89": 0,
        "0.70-0.79": 0,
        "0.50-0.69": 0,
        "0.30-0.49": 0,
        "0.00-0.29": 0,
    }
    l1_counts: dict[str, int] = defaultdict(int)
    l2_counts: dict[str, int] = defaultdict(int)
    l3_counts: dict[str, int] = defaultdict(int)

    for row in labeled_rows:
        method = str(row.get("match_method", "unknown"))
        method_counts[method] += 1

        conf = float(row.get("confidence", 0))
        if conf >= 0.90:
            confidence_buckets["0.90-1.00"] += 1
        elif conf >= 0.80:
            confidence_buckets["0.80-0.89"] += 1
        elif conf >= 0.70:
            confidence_buckets["0.70-0.79"] += 1
        elif conf >= 0.50:
            confidence_buckets["0.50-0.69"] += 1
        elif conf >= 0.30:
            confidence_buckets["0.30-0.49"] += 1
        else:
            confidence_buckets["0.00-0.29"] += 1

        l1_name = str(row.get("l1_name", "Unknown"))
        l2_name = str(row.get("l2_name", "Unknown"))
        l3_code = str(row.get("l3_code", "UNKNOWN"))
        l1_counts[l1_name] += 1
        l2_counts[l2_name] += 1
        l3_counts[l3_code] += 1

    # Unique L3 codes used
    l3_unique = len(l3_counts)

    # Average confidence
    avg_conf = sum(float(r.get("confidence", 0)) for r in labeled_rows) / max(total, 1)

    stats: dict[str, Any] = {
        "total_records": total,
        "unique_l3_categories_used": l3_unique,
        "average_confidence": round(avg_conf, 4),
        "match_method_distribution": dict(
            sorted(method_counts.items(), key=lambda x: x[1], reverse=True)
        ),
        "confidence_distribution": confidence_buckets,
        "l1_distribution": dict(
            sorted(l1_counts.items(), key=lambda x: x[1], reverse=True)
        ),
        "l2_distribution": dict(
            sorted(l2_counts.items(), key=lambda x: x[1], reverse=True)
        ),
        "top_30_l3": dict(
            sorted(l3_counts.items(), key=lambda x: x[1], reverse=True)[:30]
        ),
    }
    return stats


# ═══════════════════════════════════════════════════════════════════════════
# CLI + MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(description="Xpenzo Dataset Labeler")
    parser.add_argument(
        "--input", type=str, default=str(DEFAULT_INPUT),
        help="Path to master_dataset.csv",
    )
    parser.add_argument(
        "--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for labeled output",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_csv = output_dir / "labeled_dataset.csv"
    output_stats = output_dir / "label_stats.json"

    # ── Load taxonomy ─────────────────────────────────────────────────
    print(f"Loading taxonomy from {TAXONOMY_PATH} ...")
    tax = Taxonomy(TAXONOMY_PATH)
    print(
        f"  Loaded: {len(tax.l3_by_code)} L3 categories, "
        f"{len(tax.brand_to_l3)} brands, "
        f"{len(tax.keyword_to_l3)} keywords"
    )

    # ── Load dataset ──────────────────────────────────────────────────
    print(f"\nLoading dataset from {input_path} ...")
    with open(input_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows: list[dict[str, str]] = list(reader)
    print(f"  Loaded: {len(rows):,} records")

    # ── Label all records ─────────────────────────────────────────────
    print("\nLabeling records (5-layer cascade) ...")
    t0 = time.time()
    labeled: list[dict[str, Any]] = []
    method_counter: dict[str, int] = defaultdict(int)

    for i, row in enumerate(rows):
        result = label_record(row, tax)
        out_row = build_output_row(row, result, tax)
        labeled.append(out_row)
        method_counter[result.method] += 1

        if (i + 1) % 100000 == 0:
            elapsed = time.time() - t0
            print(f"  {i + 1:>8,} / {len(rows):,}  ({elapsed:.1f}s)")

    elapsed = time.time() - t0
    print(f"  Done: {len(labeled):,} records labeled in {elapsed:.1f}s")

    # Show method breakdown
    print("\n  Match method breakdown:")
    for method, count in sorted(
        method_counter.items(), key=lambda x: x[1], reverse=True
    ):
        pct = count / len(labeled) * 100
        print(f"    {method:25s}  {count:>8,}  ({pct:5.1f}%)")

    # ── Write labeled CSV ─────────────────────────────────────────────
    print(f"\nWriting labeled CSV to {output_csv} ...")
    with open(output_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(labeled)
    size_mb = output_csv.stat().st_size / (1024 * 1024)
    print(f"  Written: {size_mb:.1f} MB")

    # ── Write stats JSON ──────────────────────────────────────────────
    print(f"Writing stats to {output_stats} ...")
    stats = compute_stats(labeled)
    with open(output_stats, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print(f"  Written: {output_stats.name}")

    # ── Summary ───────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("LABELING COMPLETE")
    print("=" * 60)
    print(f"  Total records:       {stats['total_records']:,}")
    print(f"  Unique L3 category:  {stats['unique_l3_categories_used']}")
    print(f"  Average confidence:  {stats['average_confidence']:.4f}")
    print(f"\n  Confidence distribution:")
    for bucket, count in stats["confidence_distribution"].items():
        pct = count / max(stats["total_records"], 1) * 100
        print(f"    {bucket}: {count:>8,}  ({pct:5.1f}%)")

    print(f"\n  Top 10 L1 categories:")
    l1_items = list(stats["l1_distribution"].items())
    for name, count in l1_items[:10]:
        pct = count / max(stats["total_records"], 1) * 100
        print(f"    {name:35s} {count:>8,}  ({pct:5.1f}%)")

    print(f"\n  Output files:")
    print(f"    {output_csv}")
    print(f"    {output_stats}")


if __name__ == "__main__":
    main()
