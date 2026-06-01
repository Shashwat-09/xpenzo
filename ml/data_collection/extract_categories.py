#!/usr/bin/env python3
"""Extract all L3 categories into a flat reference file."""
import json

with open('ml/taxonomy/category_taxonomy.json', 'r', encoding='utf-8') as f:
    tax = json.load(f)

lines = []
for cat in tax['categories']:
    l1 = cat['l1_name']
    l1_code = cat['l1_code']
    for sub in cat['subcategories']:
        l2 = sub['l2_name']
        l2_code = sub['l2_code']
        for mc in sub['micro_categories']:
            kw = ';'.join(mc.get('keywords', []))
            em = ';'.join(mc.get('example_merchants', []))
            lines.append(f"{l1_code}|{l1}|{l2_code}|{l2}|{mc['l3_code']}|{mc['l3_name']}|{kw}|{em}")

with open('ml/data_collection/all_l3_categories.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print(f"Extracted {len(lines)} L3 categories")
