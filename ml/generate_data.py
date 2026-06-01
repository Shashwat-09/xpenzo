"""
generate_data.py — Synthetic Indian UPI transaction data generator for Xpenzo CHT model training.

Run:
    python generate_data.py --output data/train.csv --n_samples 200000

Generates labeled rows with columns:
    merchant_name, upi_id, amount, timestamp, l1_label, l2_label, l3_label
"""

import argparse
import random
import csv
import math
from datetime import datetime, timedelta

# ─────────────────────────────────────────────────────────────────────────────
# CATEGORY TAXONOMY  (15 L1 → 80 L2 → 520 L3, sampled to ~50 micro here)
# ─────────────────────────────────────────────────────────────────────────────

TAXONOMY = {
    "Food & Dining": {
        "Restaurant": [
            "North Indian Restaurant", "South Indian Restaurant", "Punjabi Dhaba",
            "Chinese Restaurant", "Pizza Place", "Fast Food", "Biryani House",
            "Seafood Restaurant", "Continental Restaurant", "Multi-cuisine",
        ],
        "Cafe": ["Coffee Shop", "Chai Tapri", "Bakery Cafe", "Juice Bar"],
        "Street Food": ["Vada Pav Stall", "Pani Puri", "Chaat Corner", "Dosa Corner"],
        "Grocery": ["Kirana Store", "Supermarket", "Vegetable Vendor", "Fruits Vendor"],
        "Alcohol": ["Wine Shop", "Beer Bar", "Liquor Store"],
        "Sweets": ["Mithai Shop", "Halwai"],
    },
    "Transport": {
        "Cab": ["Ola", "Uber", "Rapido", "InDrive"],
        "Auto": ["Auto Rickshaw", "E-Rickshaw"],
        "Fuel": ["Petrol Pump", "CNG Station", "Diesel Pump"],
        "Metro/Bus": ["Metro Recharge", "BEST Bus", "KSRTC", "City Bus"],
        "Parking": ["Parking Fee", "Mall Parking"],
        "Train": ["IRCTC Ticket", "Local Train"],
    },
    "Shopping": {
        "Clothing": ["Apparel Store", "Designer Boutique", "Saree Shop", "Sportswear"],
        "Electronics": ["Mobile Store", "Laptop Shop", "Electronics Retail"],
        "Online": ["Amazon Order", "Flipkart Order", "Meesho", "Myntra"],
        "Home": ["Furniture Store", "Home Decor", "Utensils Shop"],
        "Books": ["Bookstore", "Stationery"],
    },
    "Bills & Utilities": {
        "Electricity": ["MSEDCL Bill", "BESCOM Bill", "Electricity Board"],
        "Mobile": ["Jio Recharge", "Airtel Recharge", "Vi Recharge", "BSNL Recharge"],
        "Internet": ["Jio Fiber", "Airtel Xstream", "ACT Broadband"],
        "Water": ["Water Bill", "BWSSB Bill"],
        "Gas": ["Gas Bill", "PNG Bill", "LPG Booking"],
        "DTH": ["Tata Sky", "Dish TV", "Sun Direct", "Airtel DTH"],
    },
    "Entertainment": {
        "Movies": ["PVR Cinemas", "INOX", "Cinepolis", "Carnival Cinemas"],
        "OTT": ["Netflix", "Amazon Prime", "Disney+ Hotstar", "SonyLIV", "Zee5"],
        "Gaming": ["Gaming Top-up", "Steam Wallet", "Google Play Games"],
        "Events": ["Concert Ticket", "Sports Ticket", "Amusement Park"],
        "Music": ["Spotify", "Apple Music", "Gaana"],
    },
    "Healthcare": {
        "Pharmacy": ["Medical Store", "Apollo Pharmacy", "MedPlus", "1mg"],
        "Hospital": ["Hospital Bill", "Clinic Fee", "Nursing Home"],
        "Doctor": ["Doctor Consultation", "Specialist Fee"],
        "Lab Tests": ["Pathology Lab", "Diagnostic Centre", "Blood Test"],
        "Ayurveda": ["Ayurvedic Store", "Homeopathy"],
    },
    "Education": {
        "School": ["School Fee", "Tuition Fee", "CBSE School"],
        "College": ["College Fee", "University Fee"],
        "Online Learning": ["Udemy", "Coursera", "Unacademy", "Byju's"],
        "Books": ["Study Material", "Coaching Books"],
        "Coaching": ["JEE Coaching", "NEET Coaching", "CA Classes"],
    },
    "Finance": {
        "Insurance": ["LIC Premium", "Health Insurance", "Car Insurance"],
        "Loan EMI": ["Home Loan EMI", "Car Loan EMI", "Personal Loan"],
        "Mutual Funds": ["SIP Payment", "Mutual Fund", "Zerodha", "Groww"],
        "Credit Card": ["Credit Card Bill", "HDFC Card", "ICICI Card"],
        "Bank Transfer": ["NEFT Transfer", "IMPS Transfer", "UPI Transfer"],
    },
    "Travel": {
        "Flight": ["Air India", "IndiGo", "SpiceJet", "Vistara", "Akasa Air"],
        "Hotel": ["OYO Rooms", "Treebo", "Hotel Booking", "FabHotels"],
        "Bus": ["RedBus", "Abhibus", "State Bus"],
        "Holiday": ["MakeMyTrip", "Goibibo", "Yatra", "Thomas Cook"],
        "Visa/Passport": ["Visa Fee", "Passport Office"],
    },
    "Personal Care": {
        "Salon": ["Hair Salon", "Barber Shop", "Unisex Salon"],
        "Spa": ["Spa Treatment", "Massage Parlour"],
        "Gym": ["Gym Membership", "Fitness Studio", "Yoga Centre"],
        "Cosmetics": ["Beauty Store", "Nykaa", "Cosmetics Shop"],
    },
    "Home": {
        "Rent": ["House Rent", "PG Rent", "Apartment Rent"],
        "Maintenance": ["Society Maintenance", "Building Maintenance"],
        "Repair": ["Plumber", "Electrician", "AC Repair", "Carpenter"],
        "Maid/Cook": ["Maid Salary", "Cook Salary"],
        "Security": ["Security Guard"],
    },
    "Social": {
        "Gift": ["Gift Purchase", "Wedding Gift", "Diwali Gift"],
        "Donation": ["Charity Donation", "Temple Donation", "NGO"],
        "Party": ["Birthday Party", "Anniversary Dinner"],
    },
    "Business": {
        "Office Supplies": ["Stationery", "Office Equipment"],
        "Software": ["SaaS Subscription", "Hosting", "Domain"],
        "Marketing": ["Ad Spend", "Facebook Ads", "Google Ads"],
        "Professional": ["Freelancer Payment", "Consultant Fee"],
    },
    "Investment": {
        "Stocks": ["Stock Purchase", "CDSL Demat", "Broker Fee"],
        "Real Estate": ["Plot Booking", "EMI Down Payment"],
        "Gold": ["Gold Purchase", "Gold Bond"],
        "Crypto": ["WazirX", "CoinDCX", "Crypto Exchange"],
    },
    "Others": {
        "Government": ["Government Fee", "Tax Payment", "Challan"],
        "Religious": ["Temple", "Church", "Mosque Donation"],
        "Miscellaneous": ["Miscellaneous", "Unknown Vendor"],
    },
}

# Merchant name templates per micro-category
MERCHANT_TEMPLATES = {
    "Punjabi Dhaba": ["Punjabi Dhaba {loc}", "Dhaba {name}", "{name} Dhaba", "Pind Dhaba {loc}"],
    "Pizza Place": ["Pizza Hut {loc}", "Dominos {loc}", "La Pinoz {loc}", "{name} Pizza"],
    "Coffee Shop": ["Starbucks {loc}", "Cafe Coffee Day {loc}", "Third Wave Coffee", "{name} Cafe"],
    "Kirana Store": ["{name} General Store", "{name} Provision Stores", "Shri {name} Kirana"],
    "Petrol Pump": ["{name} Petrol Pump", "HP Petrol Bunk", "Indian Oil {loc}", "BPCL Pump"],
    "Ola": ["Ola Cabs", "Ola Electric", "OLA"],
    "Uber": ["Uber India", "UBER"],
    "Apollo Pharmacy": ["Apollo Pharmacy {loc}", "Apollo Medicals"],
    "LIC Premium": ["LIC India", "LIC Premium", "Life Insurance Corp"],
    "IndiGo": ["IndiGo Airlines", "INDIGO", "Interglobe Aviation"],
}

INDIAN_NAMES = ["Ram", "Shyam", "Ravi", "Mohan", "Suresh", "Ganesh", "Vijay", "Kumar", "Patel", "Singh"]
INDIAN_LOCATIONS = ["CP", "Malad", "Andheri", "Bandra", "Koramangala", "Indiranagar", "Connaught Place",
                    "MG Road", "Sector 18", "Hitech City", "Anna Nagar", "T Nagar", "Salt Lake"]

UPI_SUFFIXES = ["@okaxis", "@oksbi", "@okicici", "@okhdfcbank", "@paytm", "@ybl", "@ibl", "@upi"]

AMOUNT_RANGES = {
    "Food & Dining": (30, 2000),
    "Transport": (15, 3000),
    "Shopping": (100, 15000),
    "Bills & Utilities": (100, 5000),
    "Entertainment": (50, 3000),
    "Healthcare": (50, 20000),
    "Education": (500, 100000),
    "Finance": (500, 100000),
    "Travel": (500, 50000),
    "Personal Care": (100, 5000),
    "Home": (2000, 50000),
    "Social": (100, 50000),
    "Business": (200, 100000),
    "Investment": (1000, 100000),
    "Others": (10, 10000),
}


def random_merchant(l3_name: str, l1_name: str) -> str:
    templates = MERCHANT_TEMPLATES.get(l3_name)
    if templates:
        t = random.choice(templates)
    else:
        variants = [
            "{name} {l3}", "{l3} {loc}", "Shri {name} {l3}",
            "{l3} Store", "{name} {l3} Shop", "{l3} Point",
        ]
        t = random.choice(variants)

    name = random.choice(INDIAN_NAMES)
    loc = random.choice(INDIAN_LOCATIONS)
    l3 = l3_name
    return t.format(name=name, loc=loc, l3=l3).strip()


def random_upi(merchant: str) -> str:
    slug = merchant.lower().replace(" ", "").replace("'", "")[:12]
    suffix = random.choice(UPI_SUFFIXES)
    # 30% chance it's a phone number UPI
    if random.random() < 0.30:
        phone = f"9{random.randint(100000000, 999999999)}"
        return phone + suffix
    return slug + suffix


def random_timestamp() -> str:
    base = datetime(2025, 1, 1)
    delta = timedelta(days=random.randint(0, 500), hours=random.randint(0, 23),
                      minutes=random.randint(0, 59))
    return (base + delta).strftime("%Y-%m-%d %H:%M:%S")


def random_amount(l1: str) -> float:
    lo, hi = AMOUNT_RANGES.get(l1, (10, 5000))
    # Log-uniform distribution (more small transactions)
    log_lo = math.log(lo + 1)
    log_hi = math.log(hi + 1)
    raw = math.exp(random.uniform(log_lo, log_hi)) - 1
    # Round to common Indian amounts
    if raw < 100:
        return round(raw, 0)
    elif raw < 1000:
        return round(raw / 10) * 10
    else:
        return round(raw / 50) * 50


def generate_dataset(n_samples: int) -> list[dict]:
    rows = []
    l1_names = list(TAXONOMY.keys())
    for _ in range(n_samples):
        l1 = random.choice(l1_names)
        l2 = random.choice(list(TAXONOMY[l1].keys()))
        l3 = random.choice(TAXONOMY[l1][l2])
        merchant = random_merchant(l3, l1)
        upi = random_upi(merchant)
        amount = random_amount(l1)
        ts = random_timestamp()
        rows.append({
            "merchant_name": merchant,
            "upi_id": upi,
            "amount": amount,
            "timestamp": ts,
            "l1_label": l1,
            "l2_label": l2,
            "l3_label": l3,
        })
    return rows


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic Xpenzo training data")
    parser.add_argument("--output", default="data/train.csv")
    parser.add_argument("--n_samples", type=int, default=200_000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)

    import os
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    print(f"Generating {args.n_samples:,} samples to {args.output}")
    rows = generate_dataset(args.n_samples)

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["merchant_name", "upi_id", "amount", "timestamp",
                                                "l1_label", "l2_label", "l3_label"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Done. {len(rows):,} rows written.")
    print(f"L1 distribution:")
    from collections import Counter
    counts = Counter(r["l1_label"] for r in rows)
    for k, v in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v:,}")


if __name__ == "__main__":
    main()
