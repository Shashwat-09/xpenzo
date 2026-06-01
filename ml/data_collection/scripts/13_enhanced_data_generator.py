#!/usr/bin/env python3
"""
13_enhanced_data_generator.py — Xpenzo Enhanced Synthetic Data Generator v2

Generates massively more diverse merchant names for ALL 520 L3 categories.
Uses domain-specific merchant databases, Indian naming patterns, UPI-style
variations, city-specific names, and aggressive augmentation.

Target: 500+ unique records per L3 category (up from ~170 synthetic).
This should bring total dataset from ~419K to ~600K+ records.

Usage:
    python 13_enhanced_data_generator.py [--min-per-category 500] [--output-dir PATH]
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
import re
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent
TAXONOMY_PATH = PROJECT_ROOT / "ml" / "taxonomy" / "category_taxonomy.json"
TRAINING_DIR = PROJECT_ROOT / "ml" / "training"
DEFAULT_OUTPUT = PROJECT_ROOT / "ml" / "data_collection" / "labeled" / "enhanced_synthetic.csv"

# ═══════════════════════════════════════════════════════════════════════════
# MASSIVE INDIAN MERCHANT NAME DATABASES
# ═══════════════════════════════════════════════════════════════════════════

# Indian first names (200+) for generating "Name's Business" patterns
INDIAN_FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan",
    "Krishna", "Ishaan", "Shaurya", "Atharv", "Advik", "Pranav", "Advaith",
    "Aarush", "Kabir", "Ritvik", "Anirudh", "Dhruv", "Arnav", "Rudra", "Vedant",
    "Shivam", "Rohan", "Kartik", "Harsh", "Dev", "Yash", "Kunal",
    "Ravi", "Suresh", "Rajesh", "Mahesh", "Ramesh", "Dinesh", "Ganesh",
    "Amit", "Sumit", "Rohit", "Mohit", "Ankit", "Nikhil", "Rahul",
    "Vijay", "Ajay", "Sanjay", "Deepak", "Ashok", "Vinod", "Manoj",
    "Priya", "Neha", "Pooja", "Sneha", "Divya", "Anjali", "Kavita",
    "Sunita", "Rekha", "Meena", "Lakshmi", "Sarita", "Geeta", "Seema",
    "Asha", "Usha", "Mamta", "Kiran", "Nisha", "Ritu", "Poonam",
    "Mukesh", "Rakesh", "Naresh", "Satish", "Girish", "Hitesh", "Jitesh",
    "Pramod", "Vinay", "Anil", "Sunil", "Pankaj", "Sachin", "Gaurav",
    "Manish", "Rajat", "Tarun", "Varun", "Abhishek", "Akash", "Vishal",
]

# Indian surnames (100+) for "Surname Business" patterns
INDIAN_SURNAMES = [
    "Sharma", "Gupta", "Kumar", "Singh", "Patel", "Jain", "Agarwal",
    "Verma", "Reddy", "Rao", "Nair", "Pillai", "Das", "Mukherjee",
    "Chatterjee", "Iyer", "Menon", "Bhat", "Deshmukh", "Kulkarni",
    "Thakur", "Yadav", "Mishra", "Tiwari", "Pandey", "Srivastava",
    "Bansal", "Mahajan", "Kapoor", "Malhotra", "Arora", "Mehra",
    "Chauhan", "Saxena", "Goel", "Mittal", "Aggarwal", "Chawla",
    "Bhatt", "Joshi", "Dubey", "Shukla", "Tripathi", "Dixit",
    "Patil", "More", "Pawar", "Jadhav", "Shinde", "Kadam",
    "Naidu", "Raju", "Prasad", "Varma", "Hegde", "Shetty",
    "Nambiar", "Kurup", "Warrier", "Panicker", "Karuppan",
    "Choudhary", "Meena", "Rathore", "Shekhawat", "Tanwar",
    "Sethi", "Bedi", "Gill", "Sandhu", "Dhillon", "Grewal",
    "Khanna", "Bajaj", "Walia", "Oberoi", "Anand", "Batra",
    "Goyal", "Khandelwal", "Lodha", "Mantri", "Saraf", "Poddar",
    "Barua", "Bora", "Chetia", "Hazarika", "Phukan", "Saikia",
]

# Indian cities with states and coords (50 cities)
INDIAN_CITIES = [
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
    {"city": "Noida", "state": "Uttar Pradesh", "lat": 28.535, "lon": 77.391},
    {"city": "Gurgaon", "state": "Haryana", "lat": 28.459, "lon": 77.027},
    {"city": "Faridabad", "state": "Haryana", "lat": 28.408, "lon": 77.317},
    {"city": "Ghaziabad", "state": "Uttar Pradesh", "lat": 28.669, "lon": 77.438},
    {"city": "Mysuru", "state": "Karnataka", "lat": 12.296, "lon": 76.639},
    {"city": "Mangaluru", "state": "Karnataka", "lat": 12.914, "lon": 74.856},
    {"city": "Nashik", "state": "Maharashtra", "lat": 19.998, "lon": 73.791},
    {"city": "Vadodara", "state": "Gujarat", "lat": 22.307, "lon": 73.181},
    {"city": "Rajkot", "state": "Gujarat", "lat": 22.302, "lon": 70.802},
    {"city": "Ludhiana", "state": "Punjab", "lat": 30.901, "lon": 75.857},
    {"city": "Amritsar", "state": "Punjab", "lat": 31.634, "lon": 74.873},
    {"city": "Agra", "state": "Uttar Pradesh", "lat": 27.176, "lon": 78.008},
    {"city": "Kanpur", "state": "Uttar Pradesh", "lat": 26.449, "lon": 80.352},
    {"city": "Allahabad", "state": "Uttar Pradesh", "lat": 25.427, "lon": 81.846},
    {"city": "Madurai", "state": "Tamil Nadu", "lat": 9.925, "lon": 78.120},
    {"city": "Tiruchirappalli", "state": "Tamil Nadu", "lat": 10.791, "lon": 78.689},
    {"city": "Jodhpur", "state": "Rajasthan", "lat": 26.239, "lon": 73.024},
    {"city": "Udaipur", "state": "Rajasthan", "lat": 24.585, "lon": 73.712},
    {"city": "Raipur", "state": "Chhattisgarh", "lat": 21.251, "lon": 81.629},
    {"city": "Vijayawada", "state": "Andhra Pradesh", "lat": 16.507, "lon": 80.647},
    {"city": "Goa", "state": "Goa", "lat": 15.496, "lon": 73.828},
    {"city": "Shimla", "state": "Himachal Pradesh", "lat": 31.105, "lon": 77.172},
    {"city": "Gangtok", "state": "Sikkim", "lat": 27.339, "lon": 88.607},
    {"city": "Imphal", "state": "Manipur", "lat": 24.817, "lon": 93.945},
    {"city": "Shillong", "state": "Meghalaya", "lat": 25.578, "lon": 91.893},
]

# City short forms used in UPI
CITY_SHORTS = {
    "Mumbai": ["MUM", "BOM", "MUMBAI"],
    "Delhi": ["DEL", "DLI", "DELHI", "NDL"],
    "Bengaluru": ["BLR", "BANG", "BLORE", "BANGALORE"],
    "Hyderabad": ["HYD", "HYDERABAD"],
    "Chennai": ["CHN", "CHENNAI", "MAA"],
    "Kolkata": ["KOL", "CCU", "KOLKATA", "CAL"],
    "Pune": ["PNQ", "PUNE"],
    "Ahmedabad": ["AMD", "AHMEDABAD"],
    "Jaipur": ["JAI", "JAIPUR"],
    "Lucknow": ["LKO", "LUCKNOW"],
    "Noida": ["NOIDA", "NOI"],
    "Gurgaon": ["GGN", "GURGAON", "GURUGRAM"],
}

# Area/locality names by city for realistic UPI names
CITY_AREAS = {
    "Mumbai": ["Andheri", "Bandra", "Juhu", "Powai", "Malad", "Borivali", "Goregaon", "Thane", "Worli", "Dadar", "Kurla", "Chembur", "Vashi", "Navi Mumbai", "Colaba", "Fort"],
    "Delhi": ["Connaught Place", "Karol Bagh", "Lajpat Nagar", "Saket", "Rajouri Garden", "Dwarka", "Nehru Place", "Vasant Kunj", "Greater Kailash", "Hauz Khas", "Chandni Chowk", "Rohini"],
    "Bengaluru": ["Koramangala", "Indiranagar", "HSR Layout", "Whitefield", "Jayanagar", "JP Nagar", "Marathahalli", "Electronic City", "Bellandur", "Yelahanka", "Malleshwaram"],
    "Hyderabad": ["Banjara Hills", "Jubilee Hills", "Gachibowli", "Madhapur", "Ameerpet", "Secunderabad", "Kukatpally", "Miyapur", "Kondapur", "HITEC City"],
    "Chennai": ["T Nagar", "Anna Nagar", "Adyar", "Velachery", "Nungambakkam", "Mylapore", "Besant Nagar", "OMR", "ECR", "Porur", "Guindy"],
    "Kolkata": ["Park Street", "Salt Lake", "New Town", "Gariahat", "Ballygunge", "Howrah", "Esplanade", "Alipore", "Lake Town", "Dum Dum"],
    "Pune": ["Koregaon Park", "Viman Nagar", "Hinjewadi", "Kothrud", "Baner", "Aundh", "Wakad", "Hadapsar", "Camp", "Deccan"],
    "Ahmedabad": ["CG Road", "Satellite", "Prahlad Nagar", "Navrangpura", "Vastrapur", "SG Highway", "Bodakdev", "Maninagar"],
    "Jaipur": ["MI Road", "C Scheme", "Vaishali Nagar", "Malviya Nagar", "Mansarovar", "Raja Park", "Tonk Road"],
    "Lucknow": ["Hazratganj", "Gomti Nagar", "Aminabad", "Alambagh", "Aliganj", "Indira Nagar"],
}

# ═══════════════════════════════════════════════════════════════════════════
# DOMAIN-SPECIFIC MERCHANT DATABASES (extensive real Indian businesses)
# ═══════════════════════════════════════════════════════════════════════════

# These are organized by L1 domain with generic templates and real brand names

DOMAIN_MERCHANTS: dict[str, dict[str, list[str]]] = {
    # ── FOOD & DINING ──────────────────────────────────────────────────
    "FD_REST_NI": ["Haldiram", "Bikanervala", "Sagar Ratna", "Moti Mahal", "Pind Balluchi", "Kake Di Hatti", "Rajinder Da Dhaba", "Gulati Restaurant", "Naivedyam", "Punjabi By Nature", "Handi Restaurant", "Bukhara", "United Coffee House", "Kwality", "Copper Chimney", "Chor Bizarre", "Dilli 32", "Punjab Grill", "Dhaba By Claridges", "Haveli", "Peshawri", "Dilli Haat", "Paranthe Wali Gali", "Sitaram Diwan Chand", "Old Delhi Pavilion", "Karims", "Al Jawahar", "Changezi Chicken", "Aslam Chicken Corner", "Havemore", "Nathu Sweets", "Evergreen Sweets", "Aggarwal Sweets", "Bikaner Sweets", "Annapurna Bhojnalaya", "Shudh Vaishno Dhaba", "Amritsari Dhaba", "Highway Dhaba", "Truck Da Dhaba", "Giani Di Hatti"],
    "FD_REST_SI": ["Saravana Bhavan", "A2B Adyar Ananda Bhavan", "Vasudev Adigas", "Murugan Idli Shop", "Shanti Sagar", "Vidyarthi Bhavan", "Mavalli Tiffin Room", "MTR", "Cafe Madras", "Dakshin", "Udupi Palace", "Udupi Krishna", "Karnataka", "Sangeeta Restaurant", "Woodlands", "Dasaprakash", "Hotel Saravana", "Sangeetha Veg", "Junior Kuppanna", "Dindigul Thalappakatti", "Anjappar", "Chettinad Restaurant", "Nair Mess", "Hotel Annapoorna", "Sri Krishna Bhavan", "Rams", "Janata Hotel", "Pai Dham", "Sri Udupi", "Konark"],
    "FD_REST_CH": ["Mainland China", "Chung Wah", "Wow China", "Bercos", "Yo China", "China Town", "Golden Dragon", "Ming Palace", "Nanking", "Chinese Wok", "Wok Express", "Asia Kitchen", "Red Lantern", "Szechwan Court", "China Gate", "Oriental Bloom", "Dragon Palace", "Fortune Cookie", "Wonton House", "Chow Mein Corner", "Hakka Noodle Bar", "WOK IN", "Chinese Room"],
    "FD_REST_CT": ["The Table", "Olive Bar", "Toast And Tonic", "Smoke House Deli", "Café Zoe", "Lido", "Le Cirque", "San Qi", "Tres", "Artusi", "Celini", "Vetro", "The Sassy Spoon", "The Bombay Canteen", "O Pedro"],
    "FD_REST_IT": ["Little Italy", "Jamie's Pizzeria", "1441 Pizzeria", "Toscano", "Alto Vino", "Olive Beach", "Sopra Cucina", "The Italian", "Fratelli", "Pomodoro", "La Piazza", "Bella Italia", "Trattoria", "Casa Piccola", "Pizza Express"],
    "FD_REST_JK": ["Guppy", "Yauatcha", "Hakkasan", "Kofuku", "Shizusan", "Fuji", "Sushi Junction", "Tsunami", "Nara Thai", "Baan Tao", "Mamagoto", "Pa Pa Ya", "Misu", "En", "Izakaya", "Seoul Garden", "Kimchi", "Gung The Palace", "Ai", "Wasabi"],
    "FD_REST_MG": ["Paradise Biryani", "Behrouz Biryani", "Pista House", "Bawarchi", "Cafe Bahar", "Shah Ghouse", "Lucky Restaurant", "Shadab", "Hotel Nayaab", "Kareem's", "Tunday Kababi", "Dastarkhwan", "Mughal Mahal", "Kebab Corner", "The Great Kabab Factory", "ITC Dum Pukht", "Lucknowi Biryani House", "Hyderabadi Biryani", "Arsalan", "Aminia", "Oudh 1590", "Biryani Blues"],
    "FD_REST_BN": ["Oh Calcutta", "6 Ballygunge Place", "Bhojohori Manna", "Kewpies", "Kasturi", "Aaheli", "Saptapadi", "Bijoli Grill", "Mitra Cafe", "Golbari", "Allen Kitchen", "Koshe Kosha", "Bhojohari Manna"],
    "FD_REST_GJ": ["Gordhan Thal", "Rajdhani", "Shree Thaker Bhojanalay", "Agashiye", "Vishalla", "Gopi Dining Hall", "Sankalp", "Purohit Thali", "Seva Cafe", "Aaswad", "Rajwadu", "Patang"],
    "FD_REST_KR": ["Paragon", "Kayees", "Thalassery Restaurant", "Fort Kochi", "Dhe Puttu", "Malabar Junction", "Cassava", "Hotel Rahmaniya", "Zam Zam", "Dakshina", "Ente Keralam", "Nalpat"],
    "FD_REST_MC": ["Barbeque Nation", "Absolute Barbecue", "AB's", "Sigree", "Pirates of Grill", "The Great Indian Dhaba", "Mainland China", "Asia Kitchen By Mainland China", "Pind Balluchi", "7 Barrel Brew Pub"],
    "FD_REST_FD": ["Indian Accent", "Bukhara", "Dum Pukht", "Masala Library", "Le Cirque", "Wasabi", "San Qi", "Avartana", "Tresind", "Varq", "Megu", "Cilantro", "Caperberry", "Table No 1"],
    "FD_REST_TH": ["Farzi Cafe", "Byg Brewski", "Toit", "Social", "Monkey Bar", "Raasta", "Sky Lounge", "Smaaash", "Lord of the Drinks", "Impresario", "True Tramm Trunk"],
    "FD_REST_BF": ["Pirates of Grill", "AB's", "Barbeque Nation", "Sigree", "Buffet Hut", "Great Buffet", "Dynasty", "Grand Trunk Road", "Feast", "Unlimited"],
    "FD_REST_OTH": ["Family Restaurant", "Hotel Bhojnalaya", "Vaishno Bhojanalaya", "Mess", "Eatery", "Kitchen", "Canteen", "Hotel", "Bhawan", "Tiffin Centre", "Food Corner", "Snack Bar"],
    "FD_FAST_BG": ["McDonald's", "Burger King", "Wendy's", "Carl's Jr", "Burger Singh", "Wat-a-Burger", "Burgerama", "JEFI Burger", "Biggies", "Watt A Burger"],
    "FD_FAST_PZ": ["Domino's", "Pizza Hut", "La Pino'z", "Oven Story", "Mojo Pizza", "Papa Johns", "Slice of Italy", "Laziz Pizza", "Chicago Pizza"],
    "FD_FAST_FC": ["KFC", "Chick King", "Chicken Republic", "Al Baik", "Nando's", "Krispy Fried Chicken", "Hot N Crispy", "Chicking", "Firangi Bake"],
    "FD_FAST_SW": ["Subway", "Quiznos", "Mr Sub", "Wrapchic", "SubKuch", "Sardarji Baksh", "Sandwich Factory"],
    "FD_FAST_IN": ["Haldiram's", "Bikanervala", "Chatar Patar", "Sev Puri", "Chaat Corner", "Jumboking", "Kaati Zone", "Honest", "Faaso's"],
    "FD_FAST_WR": ["Faasos", "Tibbs Frankie", "Kathi Junction", "Roll Express", "Wrap It Up", "Shawarma King", "Al Baba", "Shawarma House"],
    "FD_FAST_MO": ["Wow Momo", "Momo King", "Momoman", "Momos Junction", "Momo Point", "Dolma Aunty Momos", "QD's", "Momo Nation Café"],
    "FD_FAST_PB": ["Sardar Pav Bhaji", "Ashok Pav Bhaji", "Cannon Pav Bhaji", "Amar Juice Centre", "Sukh Sagar", "Mamledar Misal", "Katakirr Misal"],
    "FD_FAST_DS": ["Dosa Plaza", "Vaango", "Sagar Ratna", "Hot Chips", "Saravana Bhavan Express", "Dosa Corner", "Masala Dosa Hub", "Rava Dosa King"],
    "FD_FAST_OTH": ["Chaat Wala", "Tikki Corner", "Fast Food Corner", "Quick Bite", "Food Express", "Snack House", "Food Junction"],
    "FD_CAFE_CH": ["Starbucks", "Café Coffee Day", "Blue Tokai", "Third Wave Coffee", "Tim Hortons", "Costa Coffee", "Barista", "Devans Coffee", "Sleepy Owl", "Bru World Cafe"],
    "FD_CAFE_IN": ["Prithvi Cafe", "Leopold Cafe", "Indian Coffee House", "Cha Bar", "Rose Cafe", "Rustique", "Artsy Cafe", "The Brew Room", "Studio Cafe"],
    "FD_CAFE_TC": ["Chai Point", "Chaayos", "MBA Chai Wala", "Chai Sutta Bar", "Tapri", "Kullhad Chai", "Cutting Chai", "Adrak Chai Stall", "Irani Chai"],
    "FD_CAFE_JB": ["Raw Pressery", "Juice Junction", "Fresh N Juici", "Jamba Juice", "Juice Lounge", "Sugarcane Juice Centre", "Nannari Juice"],
    "FD_CAFE_DS": ["Baskin Robbins", "Naturals", "Havmor", "Cream Stone", "Kwality Walls", "Amul Parlor", "Ibaco", "Roll Over", "Giani Ice Cream"],
    "FD_CAFE_BK": ["Monginis", "Karachi Bakery", "Iyengar Bakery", "Theobroma", "L'Opera", "Hot Breads", "Merwans", "Kayani Bakery", "Wenger's"],
    "FD_CAFE_BC": ["The Baker's Dozen", "Birdy's", "La Folie", "Le 15 Patisserie", "Mag Street Bread Co", "Suzette", "Artisan Bakehouse"],
    "FD_CAFE_OTH": ["Coffee House", "Tea Room", "Cafe Corner", "Beverage Hub", "Refreshment Centre"],
    "FD_STRT_CT": ["Chaat Bhandar", "Chaat King", "Ram Chaat", "Gopi Chaat", "Atul Chaat", "Bengali Chaat", "Dilli Chaat", "Prince Chaat"],
    "FD_STRT_VD": ["Ashok Vada Pav", "Jumbo Vada Pav", "Goli Vada Pav", "Singla Samosa", "Samosa Junction", "Samosa Wala", "Hot Samosa Corner"],
    "FD_STRT_GP": ["Pani Puri Wala", "Golgappa King", "Puchka Corner", "Bhel Puri Stand", "Gupchup Centre"],
    "FD_STRT_SN": ["Bhajia House", "Pakora King", "Kachori Wala", "Jalebi Wala", "Tikki Corner", "Bhel Corner", "Chole Bhature Wala"],
    "FD_STRT_OTH": ["Street Food Corner", "Thela", "Food Stall", "Chowk Food", "Street Kitchen"],
    "FD_DLVR_ZO": ["Zomato", "ZOMATO ORDER", "Zomato Pro", "ZOMATO GOLD", "Zomato Del", "Zomato Hyperpure"],
    "FD_DLVR_SW": ["Swiggy", "SWIGGY ORDER", "Swiggy Instamart", "Swiggy One", "Swiggy Dineout"],
    "FD_DLVR_OTH": ["EatSure", "Box8", "FreshMenu", "Rebel Foods", "Licious", "DoorDash", "Uber Eats"],
    "FD_GROC_SM": ["DMart", "Big Bazaar", "Reliance Fresh", "Reliance Smart", "Spencer's", "Star Bazaar", "More Supermarket", "Spar", "Ratnadeep", "Heritage Fresh", "Nilgiris"],
    "FD_GROC_KR": ["General Store", "Kirana Store", "Provision Store", "Ration Shop", "Grocery Shop", "Daily Needs", "Sahakari Bhandar"],
    "FD_GROC_OR": ["Organic Tattva", "24 Mantra", "Pro Nature", "Organic India", "Conscious Food", "Down To Earth", "Pristine Organics"],
    "FD_GROC_ON": ["BigBasket", "Blinkit", "Zepto", "JioMart", "Amazon Fresh", "Swiggy Instamart", "Dunzo Daily", "BBDaily"],
    "FD_GROC_VF": ["Sabziwala", "Fruit Wala", "Mandi Market", "Fresh Vegetables", "Phoolwala", "Fruit Shop", "Sabzi Mandi"],
    "FD_GROC_DP": ["Amul Parlor", "Mother Dairy", "Nandini Milk", "Verka", "Dairy Shop", "Paneer Wala", "Aarey Milk", "Kwality"],
    "FD_GROC_MT": ["Licious", "FreshToHome", "Zappfresh", "TenderCuts", "Meat Wala", "Fish Market", "Mutton Shop", "Chicken Centre"],
    "FD_GROC_OTH": ["Dry Fruit Shop", "Spice Shop", "Masala Store", "Namkeen Shop", "Oil Mill", "Atta Chakki"],
    "FD_ALC_BM": ["Toit", "Byg Brewski", "Arbor Brewing", "Windmills Craftworks", "Doolally", "White Owl", "Gateway Taproom", "The Irish House"],
    "FD_ALC_WS": ["TASMAC", "Wine Shop", "Theka", "Government Liquor Shop", "English Wine Shop", "ABC Shop"],
    "FD_ALC_NB": ["Kitty Su", "Trilogy", "Playboy Club", "Privee", "Lust By Bar", "Aer Lounge", "Sky Bar"],
    "FD_ALC_OTH": ["Bar And Restaurant", "Permit Room", "Toddy Shop", "Country Liquor", "Ahata"],
    "FD_CATR_WD": ["Brijwasi Caterers", "Shubham Caterers", "Sharma Caterers", "Rajbhog Caterers", "Wedding Kitchen", "Shaadi Caterers"],
    "FD_CATR_CP": ["Corporate Kitchen", "Office Tiffin", "Catering Service", "Bulk Food Order", "Event Caterers"],
    "FD_CATR_TB": ["Tiffin Service", "Dabba Wala", "Meal Box", "Home Kitchen", "Cloud Kitchen", "Lunch Box", "Ghar Ka Khana"],
    "FD_CATR_SD": ["Haldiram Sweet Shop", "Bikaner Sweet", "Bengali Sweet House", "Ganguram", "K C Das", "Nathu Sweets", "Dry Fruit Corner"],
    "FD_CATR_OTH": ["Party Caterer", "Banquet Kitchen", "Function Catering", "Outdoor Catering"],

    # ── SHOPPING ───────────────────────────────────────────────────────
    "SH_CLTH_MM": ["Van Heusen", "Peter England", "Raymond", "Allen Solly", "Louis Philippe", "Arrow", "Blackberrys", "Park Avenue", "Indian Terrain", "Mufti"],
    "SH_CLTH_WM": ["Biba", "W", "Aurelia", "Global Desi", "AND", "FabIndia", "Soch", "Imara", "Libas", "MAX Fashion"],
    "SH_CLTH_KD": ["Max Kids", "Mothercare", "FirstCry Store", "Hopscotch", "Babyhug", "Lilliput", "Gini & Jony", "UCB Kids"],
    "SH_CLTH_WD": ["Manyavar", "Mohey", "Meena Bazaar", "Kalki Fashion", "Sabyasachi", "Anita Dongre", "Nalli Silk Sarees", "Pothys"],
    "SH_CLTH_SP": ["Nike", "Adidas", "Puma", "Reebok", "Skechers", "Asics", "Decathlon", "Under Armour"],
    "SH_CLTH_LX": ["Gucci", "Louis Vuitton", "Zara", "H&M", "Marks Spencer", "Uniqlo", "Sabyasachi", "Good Earth"],
    "SH_CLTH_TL": ["Nalli Silks", "Pothys", "Kalyan Silks", "Chennai Silks", "Jayalakshmi Silks", "Mysore Silk", "Kanjeevaram House"],
    "SH_CLTH_FC": ["Raymond Custom", "Brooks Brothers", "Arvind Store", "Bombay Shirt Company", "Tailoring Shop", "Master Tailor"],
    "SH_CLTH_SD": ["Pantaloons", "Shoppers Stop", "Lifestyle", "Central", "Westside", "Brand Factory", "FBB"],
    "SH_CLTH_OTH": ["Cloth Store", "Garment Shop", "Readymade Shop", "Fancy Cloth Store", "Textile Shop"],
    "SH_ELEC_MB": ["Samsung Store", "Apple Store", "iStore", "Croma Mobile", "Reliance Digital Mobile", "Sangeetha Mobiles", "Poorvika Mobiles", "UniverCell", "Hotspot"],
    "SH_ELEC_LP": ["HP World", "Dell Exclusive", "Lenovo Store", "Asus Store", "Apple Authorised", "Croma Laptops"],
    "SH_ELEC_HA": ["LG Shoppe", "Samsung Digital Plaza", "Bajaj Electronics", "Viveks", "Girias", "Pai International"],
    "SH_ELEC_AC": ["Mobile Cover Shop", "Accessories Hub", "CaseKart", "Mobile Point", "Gadget Hub"],
    "SH_ELEC_CM": ["Canon Image Square", "Nikon Store", "Sony Centre", "Camera House", "Photography Shop"],
    "SH_ELEC_GM": ["Game4U", "Gaming Hub", "PlayStation Store", "Xbox Store", "Steam", "Epic Games"],
    "SH_ELEC_OTH": ["Electronics Shop", "Gadget Store", "Tech Store", "Computer Shop", "IT Store"],
    "SH_ONLN_AZ": ["Amazon", "AMAZON IN", "Amazon Pay", "Amazon Fresh", "Amazon Prime", "AMZN IN"],
    "SH_ONLN_FK": ["Flipkart", "FLIPKART COM", "Flipkart Pay", "FK Grocery"],
    "SH_ONLN_MN": ["Myntra", "MYNTRA COM", "Myntra Fashion", "Myntra End Reason"],
    "SH_ONLN_JD": ["JioMart", "Jio Store", "JIOMART ORDER"],
    "SH_ONLN_NP": ["Nykaa", "NYKAA COM", "Nykaa Fashion", "Nykaa Man"],
    "SH_ONLN_SN": ["Snapdeal", "SNAPDEAL COM", "Snapdeal Gold"],
    "SH_ONLN_MS": ["Meesho", "MEESHO COM", "Meesho Supply"],
    "SH_ONLN_OTH": ["Ajio", "Tata CLiQ", "Limeroad", "Koovs", "Bewakoof", "Club Factory", "ShopClues"],
    "SH_JWLY_GD": ["Tanishq", "Kalyan Jewellers", "Malabar Gold", "Joyalukkas", "PC Jeweller", "Senco Gold", "TBZ", "GRT Jewellers"],
    "SH_JWLY_SL": ["Tanishq Silver", "Mia by Tanishq", "Silver Palace", "Silver Filigree", "Giva"],
    "SH_JWLY_AR": ["Amrapali", "Tribe by Amrapali", "Voylla", "Sukkhi", "Fashion Jewellery", "Imitation Jewellery"],
    "SH_JWLY_WC": ["Titan", "Fastrack", "Casio", "Fossil", "Timex", "Sonata", "HMT", "Rado"],
    "SH_JWLY_OTH": ["Jewellery Shop", "Gold Palace", "Diamond Store", "Ornament House"],
    "SH_HOME_FR": ["Urban Ladder", "Pepperfry", "Godrej Interio", "Hometown", "Ikea", "WoodenStreet", "Durian"],
    "SH_HOME_KT": ["Prestige Xclusive", "Borosil Store", "Hawkins", "Stovekraft", "Kitchen Essentials", "Vinod Cookware"],
    "SH_HOME_DC": ["Home Centre", "Chumbak", "Elvy", "Good Earth", "Nicobar", "Green Decor"],
    "SH_HOME_BD": ["Sleepwell", "Duroflex", "Wakefit", "Kurlon", "Nilkamal Sleep", "Sunday Mattress"],
    "SH_HOME_HD": ["Asian Paints", "Berger Paints", "Dulux", "Hardware Store", "Paint Shop", "Building Material", "Cement Store"],
    "SH_HOME_OTH": ["Home Store", "Household Shop", "Utility Store", "Home Furnishing"],
    "SH_BOOK_BS": ["Crossword", "Om Book Shop", "Landmark", "Oxford Bookstore", "Higginbothams", "Sapna Book House"],
    "SH_BOOK_ST": ["Chhota Book Shop", "Student Store", "Stationery Mart", "Pen Paper", "Office Store"],
    "SH_BOOK_ON": ["Amazon Books", "Flipkart Books", "Books Online", "Kindle Store"],
    "SH_BOOK_OTH": ["Book Depot", "Library Shop", "Magazine Stall", "Newspaper Shop"],
    "SH_FTWR_BR": ["Bata", "Metro Shoes", "Mochi", "Liberty", "Khadims", "Relaxo", "Action Shoes"],
    "SH_FTWR_SP": ["Nike", "Adidas Originals", "Puma", "Reebok Outlet", "New Balance", "Asics"],
    "SH_FTWR_LX": ["Clarks", "Hush Puppies", "Woodland", "Red Tape", "Arrow Footwear"],
    "SH_FTWR_OTH": ["Chappal Shop", "Shoe Store", "Footwear Shop", "Sandal House"],
    "SH_PET_FD": ["Pedigree", "Royal Canin", "Drools", "Farmina", "Pet Food Store"],
    "SH_PET_AC": ["Heads Up For Tails", "PetSmart", "Petshop", "Vet Pharma", "Pet Accessories"],
    "SH_PET_VT": ["Pet Clinic", "Veterinary Hospital", "Animal Doctor", "Pet Care Centre"],
    "SH_PET_OTH": ["Pet Shop", "Aquarium", "Bird Shop", "Pet Store"],

    # ── HEALTHCARE ─────────────────────────────────────────────────────
    "HC_HOSP_MS": ["Apollo Hospital", "Fortis Hospital", "Max Hospital", "Medanta", "Narayana Health", "Manipal Hospital", "AIIMS", "Kokilaben Hospital", "Lilavati Hospital", "Breach Candy Hospital"],
    "HC_HOSP_GV": ["Government Hospital", "Civil Hospital", "District Hospital", "PHC", "CHC", "ESI Hospital", "Railway Hospital", "Municipal Hospital"],
    "HC_HOSP_PC": ["Clinic", "Polyclinic", "Health Centre", "Medical Centre", "Nursing Home", "Doctor Clinic"],
    "HC_HOSP_EY": ["Shankar Netralaya", "LV Prasad Eye", "Dr Agarwals Eye", "Centre For Sight", "Vasan Eye Care", "LVPEI"],
    "HC_HOSP_DN": ["Clove Dental", "Sabka Dentist", "Apollo Dental", "Dental Solutions", "Smile Dental", "MyDentist"],
    "HC_HOSP_AY": ["Kottakkal Arya Vaidya", "Patanjali", "Kerala Ayurveda", "Jiva Ayurveda", "Vaidyaratnam"],
    "HC_HOSP_MH": ["NIMHANS", "Mpower", "Cadabams", "Vandrevala Foundation", "iCall", "Mind Clinic"],
    "HC_PHRM_RC": ["Apollo Pharmacy", "MedPlus", "Netmeds", "1mg", "Frank Ross", "Noble Plus", "Medical Store"],
    "HC_PHRM_ON": ["PharmEasy", "1mg", "Netmeds", "Tata 1mg", "MediBuddy Pharmacy", "Amazon Pharmacy"],
    "HC_PHRM_MH": ["Jan Aushadhi", "Pradhan Mantri", "Generic Medicine", "PM Bhartiya Jan Aushadhi"],
    "HC_PHRM_AM": ["Ayurvedic Store", "Homeopathy Shop", "Patanjali Store", "Himalaya Store", "Hamdard"],
    "HC_PHRM_OTH": ["Chemist", "Drug Store", "Dawakhana", "Medicine Shop"],
    "HC_DIAG_BL": ["SRL Diagnostics", "Dr Lal PathLabs", "Thyrocare", "Metropolis", "Suburban Diagnostics", "iGenetic"],
    "HC_DIAG_IM": ["Max Imaging", "Mahajan Imaging", "Star Imaging", "X-Ray Centre", "CT Scan Centre", "MRI Centre"],
    "HC_DIAG_FB": ["Health Check Centre", "Full Body Checkup", "Preventive Health", "Executive Health Check"],
    "HC_DIAG_OTH": ["Diagnostic Centre", "Lab", "Pathology", "Test Centre"],
    "HC_SPEC_DR": ["Dermatologist", "Skin Clinic", "Kaya Clinic", "VLCC Derma", "Skin Solutions"],
    "HC_SPEC_GY": ["Gynecologist", "Maternity Hospital", "Womens Hospital", "Cloudnine", "Motherhood Hospital"],
    "HC_SPEC_PD": ["Children Hospital", "Paediatric Clinic", "Child Specialist", "Rainbow Hospital"],
    "HC_SPEC_OR": ["Orthopedic Hospital", "Bone And Joint", "Spine Clinic", "Joint Replacement Centre"],
    "HC_SPEC_CD": ["Heart Hospital", "Cardiac Centre", "Cardiologist", "Heart Foundation"],
    "HC_SPEC_OTH": ["Specialist Doctor", "Consultant", "ENT Clinic", "Neurologist", "Urologist"],
    "HC_WELL_YG": ["Yoga Studio", "Art Of Living", "Isha Yoga", "Body Art Yoga", "Yoga Shala"],
    "HC_WELL_OTH": ["Wellness Centre", "Health Hub", "Nature Cure", "Rehab Centre"],

    # ── EDUCATION ──────────────────────────────────────────────────────
    "ED_HIGH_CF": ["IIT Fee", "NIT Fee", "University Fee", "College Fee", "Engineering College", "Medical College", "BIT", "VIT", "SRM", "Manipal University"],
    "ED_HIGH_HF": ["Hostel Fee", "PG Rent", "Mess Fee", "Hostel Accommodation", "Student Housing"],
    "ED_HIGH_EX": ["NTA", "UGC NET", "GATE Fee", "JEE Application", "NEET Fee", "CAT Fee", "UPSC Fee"],
    "ED_HIGH_SA": ["IDP Education", "Leverage Edu", "Yocket", "StudyAbroad", "ETS TOEFL", "British Council IELTS"],
    "ED_HIGH_OTH": ["University", "College", "Higher Education", "Degree College"],
    "ED_SCHL_TF": ["School Fee", "DPS", "Kendriya Vidyalaya", "DAV School", "Ryan International", "Amity School"],
    "ED_SCHL_BK": ["NCERT", "S Chand", "RD Sharma", "Arihant Books", "Navneet"],
    "ED_SCHL_UN": ["School Uniform", "Uniform Shop", "School Dress", "Scholar Uniform"],
    "ED_SCHL_XC": ["School Trip", "Picnic Fee", "Sports Day", "Annual Function", "Extra Curricular"],
    "ED_SCHL_OTH": ["School", "Vidyalaya", "Shiksha Niketan", "Public School"],
    "ED_COACH_EN": ["FIITJEE", "Allen Career", "Resonance", "Aakash Institute", "Vidyamandir Classes", "Narayana"],
    "ED_COACH_UP": ["Vajiram", "Drishti IAS", "Vision IAS", "Shankar IAS", "Forum IAS"],
    "ED_COACH_MA": ["Music Class", "Dance Academy", "Art School", "Vidyarthi Drawing", "Carnatic Music Class", "Kathak Dance"],
    "ED_COACH_LN": ["British Council", "Alliance Francaise", "Goethe Institut", "English Speaking Course", "IELTS Coaching"],
    "ED_COACH_SK": ["Skill India", "NSDC", "Coding Bootcamp", "Digital Marketing Course", "Data Science Academy"],
    "ED_COACH_OTH": ["Coaching Centre", "Tuition Class", "Tutorial", "Sir Classes"],
    "ED_ONLN_IN": ["BYJU'S", "Unacademy", "Vedantu", "Physics Wallah", "Toppr", "Meritnation"],
    "ED_ONLN_GL": ["Coursera", "Udemy", "edX", "LinkedIn Learning", "Khan Academy"],
    "ED_ONLN_PR": ["Google Certification", "AWS Training", "Microsoft Cert", "Simplilearn", "UpGrad", "Great Learning"],
    "ED_ONLN_WS": ["Workshop Fee", "Masterclass", "Webinar", "Seminar Fee", "Conference"],
    "ED_ONLN_OTH": ["Online Course", "E-Learning", "Digital Course", "Virtual Class"],

    # ── TRANSPORTATION ─────────────────────────────────────────────────
    "TR_CAB_OA": ["Ola", "OLA CABS", "Ola Auto", "Ola Mini", "Ola Prime"],
    "TR_CAB_UB": ["Uber", "UBER INDIA", "Uber Go", "Uber Auto", "Uber XL"],
    "TR_CAB_RP": ["Rapido", "RAPIDO BIKE", "Rapido Auto"],
    "TR_CAB_LC": ["Meru Cabs", "Savaari", "Mega Cabs", "Easy Cabs", "City Taxi"],
    "TR_CAB_AT": ["Auto Rickshaw", "Auto Stand", "Digital Auto", "Namma Yatri Auto"],
    "TR_CAB_OTH": ["Taxi", "Cab Service", "Hire Car", "Rental Car"],
    "TR_FUEL_PT": ["HP Petrol Pump", "Indian Oil", "Bharat Petroleum", "Shell", "Reliance Petrol"],
    "TR_FUEL_EV": ["Tata Power EV", "Ather Grid", "ChargeZone", "Fortum Charge", "EESL Charge"],
    "TR_FUEL_CNG": ["CNG Station", "Adani Gas", "IGL CNG", "Mahanagar Gas CNG", "Gujarat Gas"],
    "TR_FUEL_OTH": ["Fuel Station", "Filling Station", "Gas Station", "Diesel Pump"],
    "TR_PARK_ML": ["Phoenix Mall Parking", "Select CityWalk Parking", "Mall Parking"],
    "TR_PARK_AP": ["Airport Parking", "DIAL Parking", "BIAL Parking"],
    "TR_PARK_SM": ["Smart Parking", "ParkPlus", "Get My Parking", "Park Easy"],
    "TR_PARK_OTH": ["Parking Lot", "Parking Zone", "Pay And Park", "Vehicle Stand"],
    "TR_MNTN_SR": ["Maruti Service", "Hyundai Service", "Tata Motors Service", "Honda Service Centre"],
    "TR_MNTN_WS": ["Car Workshop", "Auto Garage", "Mechanic Shop", "GoMechanic"],
    "TR_MNTN_TR": ["CEAT Tyres", "MRF Tyres", "Apollo Tyres", "JK Tyre Shoppe", "Tyre Wala"],
    "TR_MNTN_CW": ["Car Wash", "3M Car Care", "Detailing Studio", "Auto Spa", "Express Car Wash"],
    "TR_MNTN_AC": ["Car Accessories", "Blaupunkt", "Car Decor", "Seat Cover Shop"],
    "TR_MNTN_OTH": ["Auto Parts", "Spare Parts", "Battery Shop", "Windshield", "Denting Painting"],
    "TR_PUBL_MR": ["IRCTC", "Indian Railways", "Metro Rail", "Delhi Metro", "Mumbai Metro", "Namma Metro"],
    "TR_PUBL_BU": ["BMTC", "DTC Bus", "MSRTC", "KSRTC", "UPSRTC", "State Bus Stand"],
    "TR_PUBL_RF": ["IRCTC Tatkal", "Premium Tatkal", "Suvidha Train", "Garib Rath"],
    "TR_PUBL_OTH": ["Bus Ticket", "Rail Ticket", "Transport Stand", "Ferry", "Auto Stand"],

    # ── TRAVEL & ACCOMMODATION ─────────────────────────────────────────
    "TV_HTLS_LX": ["Taj Hotel", "Oberoi", "ITC Hotels", "Leela Palace", "JW Marriott", "The Lalit", "Hyatt"],
    "TV_HTLS_MD": ["Lemon Tree", "Ginger Hotel", "Ibis", "Fortune Hotel", "Pride Hotel", "Hotel Sarovar"],
    "TV_HTLS_BG": ["OYO", "FabHotel", "Treebo", "RedDoorz", "Zostel", "Backpacker Hostel", "Goibibo Hotel"],
    "TV_HTLS_HH": ["Airbnb", "Homestay", "PG Accommodation", "Farm Stay", "Guest House", "Cottage Stay"],
    "TV_HTLS_RS": ["Club Mahindra", "Sterling Holiday", "ITDC Resort", "Clarks Resort"],
    "TV_HTLS_OTH": ["Lodge", "Dharamshala", "Sarai", "Rest House", "Circuit House"],
    "TV_FLIT_DM": ["IndiGo", "SpiceJet", "Air India", "Vistara", "AirAsia India", "Go First", "Akasa Air"],
    "TV_FLIT_IN": ["Emirates", "Singapore Airlines", "Qatar Airways", "Lufthansa", "British Airways", "Thai Airways"],
    "TV_FLIT_BP": ["MakeMyTrip", "Goibibo", "Yatra", "Cleartrip", "EaseMyTrip", "Ixigo"],
    "TV_FLIT_OTH": ["Flight Booking", "Airline Ticket", "Airport", "Aviation"],
    "TV_RAIL_IR": ["IRCTC", "Indian Railways", "12 Rajdhani Express", "Shatabdi Express"],
    "TV_RAIL_TT": ["IRCTC Tatkal", "Premium Tatkal", "Suvidha Fare"],
    "TV_RAIL_OTH": ["Rail Ticket", "Train Booking", "Railway Counter"],
    "TV_BUS_RD": ["RedBus", "REDBUS TICKET", "RedBus Booking"],
    "TV_BUS_PV": ["VRL Travels", "SRS Travels", "KSRTC", "Orange Travels", "Paulo Travels", "Neeta Travels"],
    "TV_BUS_OTH": ["Bus Stand", "Bus Depot", "Bus Ticket Counter"],
    "TV_TOUR_PK": ["Thomas Cook", "Cox And Kings", "SOTC", "Veena World", "Kesari Tours", "MakeMyTrip Holiday"],
    "TV_TOUR_GD": ["Tour Guide", "Heritage Walk", "City Tour", "Sightseeing"],
    "TV_TOUR_AD": ["Thrillophilia", "Zostel Adventures", "Trekking Group", "Adventure Sports", "Bungee India"],
    "TV_TOUR_TF": ["Visa Fee", "Passport Office", "Travel Insurance", "Foreign Exchange", "Thomas Cook Forex"],
    "TV_TOUR_OTH": ["Travel Agency", "Tourism Office", "Holiday Package"],
    "TV_RENT_CR": ["Zoomcar", "Revv", "Myles", "Avis India", "Hertz India"],
    "TV_RENT_BK": ["Bounce", "Vogo", "Yulu", "Royal Brothers", "ONN Bikes"],
    "TV_RENT_OTH": ["Rental Vehicle", "Self Drive Car", "Vehicle Hire"],

    # ── UTILITIES & BILLS ──────────────────────────────────────────────
    "UT_ELEC_EB": ["BSES", "Tata Power", "MSEDCL", "BESCOM", "CESC", "TNEB", "UHBVN", "PSPCL", "KSEB"],
    "UT_ELEC_PP": ["Prepaid Meter", "Electricity Recharge", "Power Prepaid"],
    "UT_ELEC_SL": ["Tata Solar", "Adani Solar", "Rooftop Solar", "Solar Panel", "Luminous Solar"],
    "UT_ELEC_OTH": ["Electricity Bill", "Power Bill", "EB Bill"],
    "UT_WATR_WB": ["Water Bill", "BWSSB", "Delhi Jal Board", "Municipal Water", "Water Tax"],
    "UT_WATR_PR": ["Water Purifier", "Kent RO", "Eureka Forbes", "Aquaguard", "Livpure", "HUL Pureit"],
    "UT_WATR_TK": ["Water Can", "Bisleri Can", "Water Tanker", "Packaged Water", "20L Can"],
    "UT_WATR_OTH": ["Water Supply", "Bore Well", "Water Connection"],
    "UT_GAS_LP": ["HP Gas", "Indane Gas", "Bharat Gas", "LPG Cylinder", "Gas Booking"],
    "UT_GAS_PN": ["IGL PNG", "Mahanagar Gas", "Gujarat Gas PNG", "Adani Gas PNG"],
    "UT_GAS_OTH": ["Gas Bill", "Cooking Gas", "Gas Agency"],
    "UT_INTW_BB": ["Airtel Broadband", "JioFiber", "ACT Fibernet", "BSNL Broadband", "Hathway", "Tata Play Fiber"],
    "UT_INTW_WF": ["WiFi Zone", "Hotspot", "Internet Cafe", "Cyber Cafe"],
    "UT_INTW_OTH": ["Internet Bill", "ISP", "Broadband Bill"],
    "UT_SUBS_NF": ["Netflix", "NETFLIX COM", "Netflix India"],
    "UT_SUBS_PT": ["Amazon Prime", "PRIME VIDEO", "Amazon Prime Video"],
    "UT_SUBS_HS": ["Disney Hotstar", "HOTSTAR", "Disney Plus", "Hotstar VIP"],
    "UT_SUBS_SP": ["Spotify", "SPOTIFY INDIA", "Spotify Premium"],
    "UT_SUBS_YT": ["YouTube Premium", "GOOGLE YOUTUBE", "YouTube Music"],
    "UT_SUBS_JC": ["JioCinema", "JIO CINEMA", "Jio Cinema Premium"],
    "UT_SUBS_OTH": ["ZEE5", "SonyLIV", "Voot", "MX Player", "ALTBalaji", "Eros Now"],
    "UT_RENT_HR": ["House Rent", "Flat Rent", "PG Rent", "Monthly Rent", "Room Rent"],
    "UT_RENT_SM": ["Society Maintenance", "Apartment Maintenance", "Building Maintenance", "RWA Fee"],
    "UT_RENT_LC": ["Locker Charges", "Bank Locker", "Safe Deposit Locker"],
    "UT_RENT_OTH": ["Property Tax", "Rental Deposit", "Security Deposit"],

    # ── TELECOM ────────────────────────────────────────────────────────
    "TC_MOBL_PR": ["Jio Recharge", "Airtel Recharge", "Vi Recharge", "BSNL Recharge", "Jio Prepaid", "Airtel Prepaid"],
    "TC_MOBL_PO": ["Jio Postpaid", "Airtel Postpaid", "Vi Postpaid", "BSNL Postpaid"],
    "TC_MOBL_IN": ["International Roaming", "ISD Pack", "International Call Pack"],
    "TC_MOBL_OTH": ["Mobile Bill", "Phone Recharge", "SIM Card", "Number Port"],
    "TC_DTH_TS": ["Tata Play", "TATA SKY", "Tata Play Binge"],
    "TC_DTH_DH": ["DishTV", "DISH TV", "Dish TV Recharge"],
    "TC_DTH_AP": ["Airtel Digital TV", "Airtel Xstream", "Airtel DTH"],
    "TC_DTH_SU": ["Sun Direct", "SUN DIRECT DTH", "Sun Direct Recharge"],
    "TC_DTH_DD": ["Free Dish", "DD Free Dish", "Doordarshan"],
    "TC_DTH_OTH": ["DTH Recharge", "Set Top Box", "Cable TV", "Cable Operator"],
    "TC_LND_VN": ["BSNL Landline", "MTNL Landline", "Airtel Landline", "Tata Tele"],
    "TC_LND_IP": ["VoIP", "Internet Phone", "Calling Card", "WiFi Calling"],
    "TC_LND_OTH": ["Landline Bill", "Telephone Bill", "Fixed Line"],
    "TC_ACC_CS": ["Phone Case", "Mobile Cover", "Screen Guard", "Tempered Glass"],
    "TC_ACC_NB": ["New Phone", "Mobile Purchase", "Smartphone", "Feature Phone"],
    "TC_ACC_RP": ["Phone Repair", "Mobile Service Centre", "Screen Repair", "iCare", "Cashify"],
    "TC_ACC_EW": ["Extended Warranty", "Phone Insurance", "Samsung Care Plus", "Apple Care"],
    "TC_ACC_OTH": ["Charger", "Earphone", "Power Bank", "Mobile Accessories"],

    # ── ENTERTAINMENT ──────────────────────────────────────────────────
    "EN_MOVS_BM": ["BookMyShow", "BOOKMYSHOW", "BMS Ticket"],
    "EN_MOVS_PV": ["PVR Cinemas", "PVR INOX", "INOX Cinemas", "INOX Leisure"],
    "EN_MOVS_MX": ["Cinepolis", "Carnival Cinemas", "Miraj Cinemas", "Rajhans Cinemas", "Wave Cinemas"],
    "EN_MOVS_SN": ["Netflix", "Amazon Prime Video", "Disney Hotstar", "ZEE5", "SonyLIV"],
    "EN_MOVS_OTH": ["Cinema Hall", "Talkies", "Movie Theatre", "Film Show"],
    "EN_MUSC_CL": ["Live Concert", "NH7 Weekender", "Sunburn Festival", "VH1 Supersonic", "Bacardi Gig"],
    "EN_MUSC_MS": ["Furtados", "Bajaao", "Music Store", "Guitar Shop", "Musical Instruments"],
    "EN_MUSC_SB": ["Spotify", "Gaana", "JioSaavn", "Apple Music", "YouTube Music", "Wynk Music"],
    "EN_MUSC_OTH": ["Music Class", "Band Booking", "DJ Hire", "Karaoke"],
    "EN_GAME_VO": ["PlayStation", "Xbox", "Nintendo", "Steam", "Epic Games", "Google Stadia"],
    "EN_GAME_MG": ["PUBG Mobile", "Free Fire", "Google Play Games", "Supercell", "Clash Royale"],
    "EN_GAME_PC": ["Steam Games", "EA Games", "Ubisoft", "Game Pass", "GeForce Now"],
    "EN_GAME_BG": ["Board Game Cafe", "Hasbro", "Mattel Games", "Ludo King"],
    "EN_GAME_OTH": ["Gaming Zone", "VR Arena", "Game Parlor", "Arcade"],
    "EN_AMPR_AT": ["Wonderla", "Imagica", "Essel World", "Ramoji Film City", "Fun City"],
    "EN_AMPR_ZO": ["Delhi Zoo", "Mysore Zoo", "Hyderabad Zoo", "Nandankanan"],
    "EN_AMPR_WP": ["Wet N Joy", "Aquatica", "Water Kingdom", "Fun N Food"],
    "EN_AMPR_OTH": ["Theme Park", "Amusement Park", "Fun Park", "Adventure Park"],
    "EN_SPRT_EV": ["IPL Match", "Cricket Match", "Football Match", "ISL", "Pro Kabaddi", "PKL"],
    "EN_SPRT_GY": ["Gold's Gym", "Cult Fit", "Anytime Fitness", "Talwalkars", "Fitness First"],
    "EN_SPRT_SP": ["Golf Club", "Tennis Court", "Badminton Court", "Swimming Pool"],
    "EN_SPRT_EQ": ["Decathlon", "Sports Station", "Nike Store", "Adidas Originals"],
    "EN_SPRT_OTH": ["Sports Club", "Stadium", "Arena", "Ground Booking"],
    "EN_ARTS_MS": ["National Museum", "Science Museum", "Salar Jung Museum", "Indian Museum", "Museum Ticket"],
    "EN_ARTS_TH": ["Prithvi Theatre", "NCPA", "Rangshankara", "Drama Theatre", "Natyam"],
    "EN_ARTS_AG": ["Art Gallery", "Kala Ghoda", "Gallery Exhibit", "Art Exhibition"],
    "EN_ARTS_OTH": ["Cultural Event", "Exhibition", "Heritage Site", "Fort Entry"],
    "EN_HOBB_PH": ["Photography", "Canon Club", "Photo Walk", "Camera Rental"],
    "EN_HOBB_GD": ["Garden Centre", "Plant Shop", "Nursery", "Seeds Shop"],
    "EN_HOBB_CK": ["Cooking Class", "Baking Workshop", "Culinary School"],
    "EN_HOBB_OTH": ["Hobby Store", "Craft Shop", "Art Supply", "DIY Store"],

    # ── FINANCE & INSURANCE ────────────────────────────────────────────
    "FI_BANK_SV": ["SBI", "HDFC Bank", "ICICI Bank", "Axis Bank", "Kotak Bank", "PNB", "Bank of Baroda"],
    "FI_BANK_FD": ["SBI FD", "HDFC FD", "Fixed Deposit", "Term Deposit", "RD"],
    "FI_BANK_NB": ["NRE Account", "NRO Account", "NRI Banking", "Foreign Account"],
    "FI_BANK_CC": ["HDFC Credit Card", "SBI Card", "ICICI Card", "Axis Card", "Amex"],
    "FI_BANK_LK": ["Bank Locker", "Locker Rent", "Locker Charges", "Safe Deposit"],
    "FI_BANK_OTH": ["Bank Charges", "Service Charge", "Annual Fee", "Processing Fee"],
    "FI_INVT_MF": ["SBI Mutual Fund", "HDFC MF", "ICICI Prudential", "Axis MF", "Groww", "Zerodha Coin"],
    "FI_INVT_ST": ["Zerodha", "Groww", "Upstox", "Angel Broking", "ICICI Direct", "Sharekhan"],
    "FI_INVT_GD": ["Sovereign Gold Bond", "Gold ETF", "Digital Gold", "MMTC Gold"],
    "FI_INVT_RD": ["Real Estate", "Property", "Flat Booking", "Plot Purchase"],
    "FI_INVT_PP": ["PPF", "NSC", "Post Office Savings", "KVP", "Sukanya Samriddhi"],
    "FI_INVT_CR": ["Bitcoin", "Crypto", "WazirX", "CoinDCX", "CoinSwitch", "ZebPay"],
    "FI_INVT_OTH": ["NPS", "Investment", "SIP", "Bonds"],
    "FI_LOAN_HL": ["Home Loan EMI", "SBI Home Loan", "HDFC Home Loan", "LIC HFL", "Bajaj Home Loan"],
    "FI_LOAN_PL": ["Personal Loan", "Bajaj Finserv", "Tata Capital", "MoneyTap", "KreditBee"],
    "FI_LOAN_EL": ["Education Loan", "Vidya Lakshmi", "Student Loan", "Study Loan"],
    "FI_LOAN_AL": ["Car Loan EMI", "Auto Loan", "Two Wheeler Loan", "Vehicle Finance"],
    "FI_LOAN_GL": ["Gold Loan", "Muthoot Finance", "Manappuram Gold", "IIFL Gold"],
    "FI_LOAN_OTH": ["Loan EMI", "Finance Company", "NBFC", "Lending"],
    "FI_INSR_LI": ["LIC", "SBI Life", "HDFC Life", "ICICI Prudential Life", "Max Life", "Bajaj Allianz Life"],
    "FI_INSR_HI": ["Star Health", "HDFC ERGO Health", "ICICI Lombard Health", "Max Bupa", "Religare Health"],
    "FI_INSR_MI": ["ICICI Lombard Motor", "Bajaj Allianz Motor", "New India Assurance", "Oriental Insurance"],
    "FI_INSR_TV": ["Travel Insurance", "TATA AIG Travel", "Bajaj Travel", "SBI Travel Insurance"],
    "FI_INSR_OTH": ["Insurance Premium", "Policy Renewal", "General Insurance"],
    "FI_CASH_AT": ["ATM Withdrawal", "Cash ATM", "SBI ATM", "HDFC ATM"],
    "FI_CASH_OTH": ["Cash Deposit", "NEFT", "RTGS", "IMPS", "Bank Transfer"],

    # ── GOVERNMENT & TAXES ─────────────────────────────────────────────
    "GV_TAX_IT": ["Income Tax", "IT Department", "TIN NSDL", "E-Filing"],
    "GV_TAX_GS": ["GST Payment", "GSTN", "GST Return", "GST Filing"],
    "GV_TAX_PT": ["Professional Tax", "PT Payment", "Employment Tax"],
    "GV_TAX_PP": ["Property Tax", "Municipal Tax", "House Tax", "Corporation Tax"],
    "GV_TAX_TT": ["TDS Payment", "TCS Payment", "Tax Deducted", "Form 26AS"],
    "GV_TAX_AT": ["Advance Tax", "Self Assessment Tax", "Challan 280"],
    "GV_TAX_OTH": ["Tax Payment", "Stamp Duty", "Registration Fee", "Cess"],
    "GV_DOCS_PS": ["Passport Office", "PSK", "Passport Seva", "RPO"],
    "GV_DOCS_DL": ["RTO", "Driving License", "Learner License", "DL Renewal", "Parivahan"],
    "GV_DOCS_RC": ["Vehicle Registration", "RC Transfer", "Road Tax", "RTO Fee"],
    "GV_DOCS_AD": ["Aadhaar Centre", "UIDAI", "Aadhaar Update", "Enrollment Centre"],
    "GV_DOCS_PN": ["PAN Card", "NSDL PAN", "UTI PAN", "PAN Correction"],
    "GV_DOCS_OTH": ["Birth Certificate", "Marriage Certificate", "Caste Certificate"],
    "GV_FINE_TF": ["Traffic Fine", "E-Challan", "Traffic Police", "Traffic Violation"],
    "GV_FINE_MF": ["Municipal Fine", "Corporation Penalty", "Building Violation", "Encroachment Fine"],
    "GV_FINE_CF": ["Court Fine", "Legal Penalty", "Judicial Fine"],
    "GV_FINE_OTH": ["Penalty Payment", "Late Fee", "Fine Payment"],
    "GV_WELF_PM": ["PM Kisan", "Mudra Loan", "Ujjwala", "Jan Dhan", "Ayushman Bharat"],
    "GV_WELF_SC": ["Scholarship", "Post Matric", "Merit Scholarship", "State Scholarship", "UGC Scholarship"],
    "GV_WELF_SB": ["Subsidy", "LPG Subsidy", "Fertilizer Subsidy", "Food Subsidy"],
    "GV_WELF_OTH": ["Government Scheme", "Welfare Payment", "Pension", "EPFO"],

    # ── FAMILY & SOCIAL ────────────────────────────────────────────────
    "FS_GIFT_ON": ["Amazon Gift Card", "Flipkart Gift Card", "Google Play Gift", "iTunes Gift Card"],
    "FS_GIFT_PH": ["Archies Gallery", "Hallmark", "Gift Shop", "Flower Shop", "Ferns N Petals", "IGP"],
    "FS_GIFT_JW": ["Tanishq Gift", "Kalyan Jewellers Gift", "Gold Coin", "Silver Coin", "Gift Jewellery"],
    "FS_GIFT_CF": ["Crowdfunding", "Ketto", "Milaap", "GoFundMe", "ImpactGuru"],
    "FS_GIFT_OTH": ["Gift", "Present", "Donation Gift", "Hamper", "Greeting Card"],
    "FS_CELB_WD": ["Wedding Hall", "Wedding Planner", "Marriage Palace", "Shaadi", "Wedding Venue"],
    "FS_CELB_BD": ["Birthday Party", "Party Hall", "Birthday Cake", "Party Decoration"],
    "FS_CELB_AN": ["Anniversary Gift", "Anniversary Dinner", "Anniversary Celebration"],
    "FS_CELB_FP": ["Diwali Shopping", "Holi Party", "Eid Shopping", "Christmas Shopping", "Pongal Gift"],
    "FS_CELB_OTH": ["Celebration", "Party", "Function", "Get Together", "Gathering"],
    "FS_RELG_TV": ["Temple Donation", "Mandir", "Devasthanam", "Tirupati", "Vaishno Devi"],
    "FS_RELG_MC": ["Mosque Donation", "Church Donation", "Gurudwara", "Dargah"],
    "FS_RELG_PG": ["Pilgrimage", "Yatra", "Chardham", "Kailash Mansarovar", "Amarnath"],
    "FS_RELG_PJ": ["Puja Samagri", "Pooja Items", "Havan Samagri", "Agarbatti", "Temple Prasad"],
    "FS_RELG_OTH": ["Religious Donation", "Dakshina", "Charity", "Sadaqah"],
    "FS_CHLD_TC": ["Toys R Us", "Hamleys", "Toy Shop", "Funskool", "Lego Store"],
    "FS_CHLD_CC": ["Day Care", "Creche", "Play School", "Montessori", "KidZee"],
    "FS_CHLD_BP": ["Baby Product", "FirstCry", "Mothercare Store", "Chicco", "Pampers"],
    "FS_CHLD_CL": ["Kids Activity", "Summer Camp", "Art Class Kids", "Swimming Kids", "Hobby Class"],
    "FS_CHLD_OTH": ["Children Store", "Kids Zone", "Play Area", "Kids Wear"],
    "FS_CHAR_NG": ["CRY", "HelpAge India", "Akshaya Patra", "GiveIndia", "Habitat"],
    "FS_CHAR_RF": ["PM CARES", "CM Relief Fund", "Red Cross", "Disaster Relief"],
    "FS_CHAR_OTH": ["Donation", "Daan", "Charity", "Social Cause", "Fund Raising"],

    # ── PERSONAL CARE & WELLNESS ───────────────────────────────────────
    "PC_SALN_MS": ["Jawed Habib", "Naturals", "Green Trends", "Toni And Guy", "Looks Salon"],
    "PC_SALN_WB": ["VLCC", "Lakme Salon", "Enrich", "Jean Claude Biguine", "Bodycraft"],
    "PC_SALN_UX": ["YLG", "Toni And Guy", "BBlunt", "Geetanjali Salon"],
    "PC_SALN_OTH": ["Beauty Parlour", "Hair Salon", "Barber Shop", "Nai Ki Dukaan"],
    "PC_SPA_AY": ["Kerala Ayurvedic Spa", "Kairali Spa", "Forest Essentials Spa", "Ayurvedic Massage"],
    "PC_SPA_TB": ["Thai Spa", "Balinese Spa", "O2 Spa", "Body Massage", "Four Fountains"],
    "PC_SPA_LX": ["Aman Spa", "ESPA", "Jiva Spa", "Kaya Kalp", "Ananda Spa"],
    "PC_SPA_OTH": ["Spa Centre", "Massage Parlour", "Wellness Spa", "Body Spa"],
    "PC_FIT_GY": ["Gold's Gym", "Cult Fit", "Anytime Fitness", "Talwalkars", "Fitness First", "CrossFit"],
    "PC_FIT_PT": ["Personal Trainer", "Home Trainer", "Fitness Coach", "PT Session"],
    "PC_FIT_YG": ["Yoga Studio", "Yoga Class", "Isha Yoga", "Art Of Living", "Power Yoga"],
    "PC_FIT_MC": ["Martial Arts", "Karate Class", "Taekwondo", "MMA", "Boxing Gym"],
    "PC_FIT_SW": ["Swimming Pool", "Swim Class", "Aqua Fitness", "Swimming Academy"],
    "PC_FIT_OTH": ["Sports Club", "Fitness Zone", "Health Club", "Gymnasium"],
    "PC_COSM_SK": ["Nykaa", "The Body Shop", "Forest Essentials", "Kama Ayurveda", "Biotique"],
    "PC_COSM_MK": ["MAC", "Lakme", "Maybelline", "L'Oreal", "Bobbi Brown", "MyGlamm"],
    "PC_COSM_HR": ["Hair Oil", "Shampoo", "Conditioner", "Hair Treatment", "Streax"],
    "PC_COSM_FR": ["Perfume", "Fragrance", "Deodorant", "Body Mist", "Zara Perfume"],
    "PC_COSM_OTH": ["Cosmetic Shop", "Beauty Store", "Personal Care Store"],
    "PC_OPTC_EG": ["Lenskart", "Titan Eye Plus", "GKB Opticals", "Lawrence Mayo", "Vision Express"],
    "PC_OPTC_CL": ["Contact Lens", "Bausch Lomb", "Acuvue", "Johnson Lens"],
    "PC_OPTC_SG": ["Sunglasses", "Ray Ban", "Oakley", "Fastrack Sunglasses"],
    "PC_OPTC_OTH": ["Optical Shop", "Eye Glass", "Spectacle Shop"],

    # ── PROFESSIONAL SERVICES ──────────────────────────────────────────
    "PS_LEGL_LC": ["Advocate", "Lawyer", "Legal Consultation", "Vakilsearch", "LegalKart"],
    "PS_LEGL_LD": ["Stamp Paper", "Notary", "Documentation", "Agreement", "Legal Document"],
    "PS_LEGL_CJ": ["Court Fee", "Judicial Stamp", "Filing Fee", "Legal Fees"],
    "PS_LEGL_OTH": ["Law Firm", "Legal Service", "Arbitration", "Mediation"],
    "PS_ACNT_CA": ["CA Fees", "Chartered Accountant", "Tax Filing", "ITR Filing", "ClearTax"],
    "PS_ACNT_TX": ["Tax Consultant", "GST Filing", "TDS Return", "Tax Advisory"],
    "PS_ACNT_AD": ["Audit Fee", "Statutory Audit", "Internal Audit", "Compliance"],
    "PS_ACNT_OTH": ["Accounting Service", "Bookkeeping", "Financial Advisory"],
    "PS_DSGN_IT": ["Interior Design", "Livspace", "HomeLane", "DesignCafe", "Decorpot"],
    "PS_DSGN_GD": ["Graphic Design", "Logo Design", "Canva Pro", "Adobe", "Design Agency"],
    "PS_DSGN_WB": ["Website Design", "Web Development", "App Development", "Digital Agency"],
    "PS_DSGN_OTH": ["Design Studio", "Creative Agency", "Freelance Designer"],
    "PS_HMSR_PL": ["Plumber", "UrbanClap Plumber", "Urban Company Plumber", "Plumbing Service"],
    "PS_HMSR_EL": ["Electrician", "Urban Company Electrician", "Electrical Service", "Wiring"],
    "PS_HMSR_CL": ["Urban Company Cleaning", "Deep Clean", "House Cleaning", "Maid Service", "HouseJoy"],
    "PS_HMSR_PT": ["Pest Control", "HiCare", "Urban Company Pest", "Terminix", "Rentokil"],
    "PS_HMSR_FR": ["Freelancer", "Gig Worker", "TaskRabbit", "UrbanClap", "Handyman"],
    "PS_HMSR_OTH": ["Home Service", "Repair Service", "Maintenance", "AMC"],

    # ── MISCELLANEOUS ──────────────────────────────────────────────────
    "MS_CASH_WD": ["ATM Cash Withdrawal", "Cash ATM", "SBI ATM Cash", "HDFC ATM Cash"],
    "MS_CASH_DP": ["Cash Deposit", "CDM Deposit", "Bank Cash Deposit"],
    "MS_CASH_OTH": ["Cash Transaction", "Cash Exchange", "Money Transfer"],
    "MS_P2P_FA": ["Family Transfer", "Sent To Family", "Mom Transfer", "Dad Transfer"],
    "MS_P2P_FR": ["Friend Transfer", "Sent To Friend", "Split Bill", "Splitwise"],
    "MS_P2P_RM": ["Room Rent Split", "Flatmate Transfer", "Roommate Bill"],
    "MS_P2P_OTH": ["UPI Transfer", "Money Sent", "Payment To", "P2P"],
    "MS_UNKN_UO": ["Unknown Merchant", "Unidentified", "MISC PAYMENT", "PAYMENT", "TXN"],
    "MS_UNKN_RC": ["Refund", "Cashback", "Reversal", "Credit Back"],
    "MS_UNKN_BD": ["Bounced", "Declined", "Failed Transaction", "Insufficient Balance"],
    "MS_UNKN_OTH": ["Other Payment", "Miscellaneous", "General", "Sundry"],
    "MS_ERND_SA": ["Salary Credit", "Monthly Salary", "Pay Credit", "Wage Credit"],
    "MS_ERND_FL": ["Freelance Payment", "Project Payment", "Gig Payment", "Contract Pay"],
    "MS_ERND_IN": ["Interest Credit", "FD Interest", "Savings Interest", "Dividend"],
    "MS_ERND_RF": ["Tax Refund", "ITR Refund", "GST Refund", "Excess Payment Refund"],
    "MS_ERND_RB": ["Cashback Reward", "Reward Points", "SuperCoin", "PayTM Cashback", "PhonePe Reward"],
    "MS_ERND_OTH": ["Income", "Earning", "Credit", "Received"],
    "MS_DEAD_BF": ["Funeral", "Cremation", "Last Rites", "Antim Yatra", "Shradh"],
    "MS_DEAD_MI": ["Memorial", "Barsi", "Death Anniversary", "Tehravi"],
    "MS_DEAD_OTH": ["Bereavement", "Condolence", "Obituary"],
}

# Templates for generating more names per domain
DOMAIN_TEMPLATES: dict[str, list[str]] = {
    "FD": ["{name}'s {kw}", "{name} {kw} {city}", "{kw} Corner", "{kw} House", "{kw} Express",
           "{kw} Hub", "{name} {kw} Restaurant", "New {name} {kw}", "Shri {name} {kw}",
           "{kw} Wala", "{kw} Palace", "{kw} Junction", "Hotel {name}", "{kw} Bhawan",
           "Sri {kw}", "Maa {kw}", "Jai {kw}", "{city} {kw}", "{kw} Point", "{kw} Centre",
           "{name} Ka {kw}", "{kw} King", "{kw} World", "Royal {kw}", "The {kw} Place",
           "{kw} Darbar", "{kw} Mahal", "New {kw} {city}", "Famous {kw}", "Original {kw}",
           "{name} And Sons {kw}", "{kw} Bhandar", "Apna {kw}"],
    "SH": ["{name} {kw}", "{kw} Mart", "{kw} Store", "{kw} Emporium", "{name}'s {kw} Shop",
           "{kw} World", "{kw} Hub", "The {kw} Shop", "{city} {kw}", "{kw} Plaza",
           "{name} {kw} Traders", "Shree {kw}", "Sri {kw} {city}", "{kw} Bazaar",
           "New {kw} Store", "{kw} Gallery", "{kw} Point", "Royal {kw}"],
    "HC": ["{name} {kw}", "Dr {name} {kw}", "{city} {kw}", "{name} {kw} Centre",
           "Shri {kw}", "{kw} Hospital", "New {kw}", "Modern {kw}", "Advanced {kw}",
           "{name} Memorial {kw}", "Sai {kw}", "Life {kw}", "Care {kw}"],
    "ED": ["{name} {kw}", "{city} {kw}", "{name} {kw} Academy", "Sri {kw} Institute",
           "The {kw}", "Modern {kw}", "National {kw}", "Indian {kw}", "{kw} Centre",
           "New {kw} {city}", "Shri {kw}"],
    "TR": ["{name} {kw}", "{city} {kw}", "{kw} Service", "Quick {kw}", "Fast {kw}",
           "City {kw}", "{kw} Zone", "{kw} Point", "Star {kw}", "Royal {kw}",
           "National {kw}", "New {kw}"],
    "TV": ["{name} {kw}", "{city} {kw}", "Hotel {name}", "{kw} Inn", "{kw} Palace",
           "The {name}", "Royal {kw}", "Golden {kw}", "Star {kw}", "Grand {kw}"],
    "UT": ["{kw}", "{city} {kw}", "{name} {kw}", "Municipal {kw}", "State {kw}"],
    "TC": ["{kw}", "{name} {kw}", "{city} {kw}", "My {kw}", "Smart {kw}"],
    "EN": ["{name} {kw}", "{city} {kw}", "New {kw}", "Star {kw}", "Royal {kw}",
           "Fun {kw}", "Big {kw}", "Metro {kw}", "The {kw}"],
    "FI": ["{name} {kw}", "{kw} {city}", "Shri {kw}", "{name} And Sons {kw}",
           "National {kw}", "Indian {kw}", "New {kw}"],
    "GV": ["{kw}", "{city} {kw}", "State {kw}", "District {kw}", "Municipal {kw}"],
    "FS": ["{name} {kw}", "{city} {kw}", "Shri {kw}", "Sri {kw}", "New {kw}",
           "Maa {kw}", "Sai {kw}"],
    "PC": ["{name}'s {kw}", "{city} {kw}", "New {kw}", "The {kw}", "{name} {kw} Studio",
           "Royal {kw}", "Star {kw}", "Modern {kw}"],
    "PS": ["{name} {kw}", "Dr {name} {kw}", "{city} {kw}", "{name} And Associates",
           "Prime {kw}", "Expert {kw}", "Pro {kw}"],
    "MS": ["{kw}", "{name} {kw}", "{kw} Transfer", "{kw} Payment"],
}

# ═══════════════════════════════════════════════════════════════════════════
# AUGMENTATION (UPI-style variations)
# ═══════════════════════════════════════════════════════════════════════════

TYPO_CHARS = "aeiounrstl"

def inject_typo(name: str) -> str:
    if len(name) < 3:
        return name
    chars = list(name)
    op = random.choice(["swap", "insert", "delete"])
    idx = random.randint(1, len(chars) - 2)
    if op == "swap" and idx < len(chars) - 1:
        chars[idx], chars[idx + 1] = chars[idx + 1], chars[idx]
    elif op == "insert":
        chars.insert(idx, random.choice(TYPO_CHARS))
    elif op == "delete":
        chars.pop(idx)
    return "".join(chars)

HINDI_VARIANTS = {
    "restaurant": ["restraunt", "restarant", "restro", "restaurnt", "resto"],
    "hospital": ["hosptal", "hosptl", "hospitl"],
    "pharmacy": ["pharmcy", "farmacy", "pharma"],
    "school": ["skool", "schl"], "college": ["colg", "collge"],
    "medical": ["medcl", "medikal"], "clinic": ["clinik", "clnic"],
    "hotel": ["hotl", "hotell"], "mart": ["mrt"],
    "store": ["stor", "stoer"], "super": ["supr", "spr"],
    "market": ["mrkt", "markt"], "centre": ["center", "centr", "sentr"],
    "service": ["servce", "srvice", "servis"],
    "enterprises": ["enterpr", "entrprs"],
    "salon": ["saloon", "saln"], "gym": ["jym", "jimm"],
    "studio": ["stdio", "stuidio"], "academy": ["acadmy", "acdmy"],
    "diagnostic": ["diagnstc", "diagnstic"],
    "insurance": ["insuranc", "insurnce"],
}

def augment_name(name: str, count: int = 8) -> list[str]:
    """Generate UPI-style noisy variants."""
    variants = {name}
    # Truncations
    if len(name) > 15:
        variants.add(name[:15])
        variants.add(name[:20])
    if len(name) > 10:
        variants.add(name[:12])
    # Abbreviations
    words = name.split()
    if len(words) > 1:
        variants.add("".join(w[0].upper() for w in words if w))
        variants.add(words[0] + " " + " ".join(w[0].upper() for w in words[1:] if w))
        if len(words) > 2:
            variants.add(words[0] + " " + words[-1])
    # Typos
    for _ in range(3):
        variants.add(inject_typo(name))
    # Case
    variants.add(name.upper())
    variants.add(name.lower())
    variants.add(name.title())
    # Hindi variants
    nl = name.lower()
    for word, alts in HINDI_VARIANTS.items():
        if word in nl:
            for alt in alts:
                variants.add(nl.replace(word, alt))
    # Strip suffixes
    for suffix in ["pvt ltd", "private limited", "llp", "& co", "(india)", "india"]:
        if nl.endswith(suffix):
            stripped = name[: -len(suffix)].strip()
            if stripped:
                variants.add(stripped)

    result = list(variants)
    random.shuffle(result)
    return result[:count]


# ═══════════════════════════════════════════════════════════════════════════
# MAIN GENERATOR
# ═══════════════════════════════════════════════════════════════════════════

OUTPUT_FIELDS = [
    "name", "brand", "cuisine", "city", "state", "lat", "lon",
    "l1_id", "l1_code", "l1_name",
    "l2_id", "l2_code", "l2_name",
    "l3_id", "l3_code", "l3_name",
    "confidence", "match_method",
]


def generate_names_for_l3(
    l3_code: str,
    l3_info: dict,
    target: int,
) -> list[str]:
    """Generate target number of unique merchant names for an L3 category."""
    l1_code = l3_info["l1_code"]
    domain_key = l1_code[:2]
    templates = DOMAIN_TEMPLATES.get(domain_key, DOMAIN_TEMPLATES["MS"])

    # Start with domain merchants if available
    base_names: set[str] = set()
    if l3_code in DOMAIN_MERCHANTS:
        for m in DOMAIN_MERCHANTS[l3_code]:
            base_names.add(m)

    # Also use taxonomy keywords and example merchants
    keywords = l3_info.get("keywords", [])
    example_merchants = l3_info.get("merchants", [])
    for m in example_merchants:
        base_names.add(m)

    # Generate from templates
    cities = [c["city"] for c in INDIAN_CITIES]
    for _ in range(target * 3):  # Over-generate, then deduplicate
        if len(base_names) >= target:
            break
        template = random.choice(templates)
        name = random.choice(INDIAN_SURNAMES)
        kw = random.choice(keywords) if keywords else l3_info["l3_name"]
        city = random.choice(cities)
        try:
            generated = template.format(name=name, kw=kw.title(), city=city)
            base_names.add(generated)
        except (KeyError, IndexError):
            pass

    # Add city-specific variations
    extra: set[str] = set()
    for bn in list(base_names)[:50]:
        city = random.choice(cities)
        area = random.choice(CITY_AREAS.get(city, [city]))
        extra.add(f"{bn} {area}")
        short = CITY_SHORTS.get(city, [city[:3].upper()])
        extra.add(f"{bn} {random.choice(short)}")
    base_names.update(extra)

    return list(base_names)[:target]


def main():
    parser = argparse.ArgumentParser(description="Enhanced Synthetic Data Generator v2")
    parser.add_argument("--min-per-category", type=int, default=500,
                        help="Minimum total records per L3 category")
    parser.add_argument("--augmentation-factor", type=int, default=6,
                        help="Augmentation variants per base name")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT),
                        help="Output CSV path")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)

    print("=" * 60)
    print("ENHANCED SYNTHETIC DATA GENERATOR v2")
    print("=" * 60)

    # Load taxonomy
    print(f"\nLoading taxonomy from {TAXONOMY_PATH}...")
    with open(TAXONOMY_PATH, "r", encoding="utf-8") as f:
        tax = json.load(f)

    l3_index: dict[str, dict] = {}
    for l1 in tax["categories"]:
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
    print(f"  Loaded {len(l3_index)} L3 categories")

    # Count existing training records
    print(f"\nCounting existing records...")
    existing: Counter = Counter()
    train_csv = TRAINING_DIR / "train.csv"
    val_csv = TRAINING_DIR / "val.csv"
    test_csv = TRAINING_DIR / "test.csv"
    for csv_file in [train_csv, val_csv, test_csv]:
        if csv_file.exists():
            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    existing[row["l3_code"]] += 1
    total_existing = sum(existing.values())
    print(f"  {total_existing:,} existing records across {len(existing)} L3 categories")

    # Determine how many more we need per category
    generation_plan: list[tuple[str, int]] = []
    for code, info in l3_index.items():
        current = existing.get(code, 0)
        if current < args.min_per_category:
            needed = args.min_per_category - current
            generation_plan.append((code, needed))

    generation_plan.sort(key=lambda x: x[1], reverse=True)
    print(f"  {len(generation_plan)} categories need more data")
    total_to_generate = sum(n for _, n in generation_plan)
    print(f"  Total records to generate: {total_to_generate:,}")

    # Generate
    print(f"\nGenerating enhanced synthetic data...")
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    total_generated = 0
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()

        for i, (code, needed) in enumerate(generation_plan):
            info = l3_index[code]
            # Generate base names
            base_count = max(20, needed // args.augmentation_factor + 10)
            base_names = generate_names_for_l3(code, info, base_count)

            records_written = 0
            for base_name in base_names:
                variants = augment_name(base_name, args.augmentation_factor)
                for variant in variants:
                    if records_written >= needed:
                        break
                    city_info = random.choice(INDIAN_CITIES)
                    lat_j = random.uniform(-0.05, 0.05)
                    lon_j = random.uniform(-0.05, 0.05)
                    record = {
                        "name": variant,
                        "brand": "",
                        "cuisine": "",
                        "city": str(city_info["city"]),
                        "state": str(city_info["state"]),
                        "lat": str(round(float(city_info["lat"]) + lat_j, 6)),
                        "lon": str(round(float(city_info["lon"]) + lon_j, 6)),
                        "l1_id": str(info["l1_id"]),
                        "l1_code": str(info["l1_code"]),
                        "l1_name": str(info["l1_name"]),
                        "l2_id": str(info["l2_id"]),
                        "l2_code": str(info["l2_code"]),
                        "l2_name": str(info["l2_name"]),
                        "l3_id": str(info["l3_id"]),
                        "l3_code": str(info["l3_code"]),
                        "l3_name": str(info["l3_name"]),
                        "confidence": "0.95",
                        "match_method": "enhanced_synthetic_v2",
                    }
                    writer.writerow(record)
                    records_written += 1
                if records_written >= needed:
                    break

            total_generated += records_written
            if (i + 1) % 50 == 0 or i == len(generation_plan) - 1:
                print(f"  [{i+1}/{len(generation_plan)}] Generated {total_generated:,} records...")

    print(f"\n{'='*60}")
    print(f"DONE! Generated {total_generated:,} new records")
    print(f"Output: {output_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
