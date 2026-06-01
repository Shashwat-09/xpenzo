"""Analyze per-category accuracy to find worst performers."""
import csv
import json
import os
from collections import Counter, defaultdict

# Load the model and run predictions? No - too heavy.
# Instead, let's analyze the data quality per category.

train_csv = 'ml/training/train.csv'
test_csv = 'ml/training/test.csv'

# Count samples per L3 in train vs test
train_l3 = Counter()
test_l3 = Counter()
train_l1 = Counter()
test_l1 = Counter()

# Track source distribution per L3
l3_methods = defaultdict(Counter)  # l3_name -> {method: count}
l3_confidence = defaultdict(list)   # l3_name -> [confidence values]

with open(train_csv, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        l3 = row['l3_name']
        l1 = row['l1_name']
        train_l3[l3] += 1
        train_l1[l1] += 1
        method = row.get('match_method', 'unknown')
        l3_methods[l3][method] += 1
        try:
            l3_confidence[l3].append(float(row.get('confidence', 0)))
        except:
            pass

with open(test_csv, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        test_l3[row['l3_name']] += 1
        test_l1[row['l1_name']] += 1

# Analyze data quality signals
print("=" * 80)
print("DATA QUALITY ANALYSIS")
print("=" * 80)

print(f"\nTotal train: {sum(train_l3.values())} | Total test: {sum(test_l3.values())}")
print(f"L3 categories: {len(train_l3)}")

# Categories with highest % of synthetic data (less diverse)
print("\n--- Categories with MOST synthetic data (worst diversity) ---")
synth_heavy = []
for l3, methods in l3_methods.items():
    total = sum(methods.values())
    synth = methods.get('synthetic', 0)
    synth_pct = synth / total * 100
    synth_heavy.append((l3, synth_pct, total, synth))

synth_heavy.sort(key=lambda x: -x[1])
print(f"{'Category':<45} {'Synth%':>7} {'Total':>7} {'Synth':>7}")
for name, pct, total, synth in synth_heavy[:30]:
    print(f"  {name:<43} {pct:6.1f}% {total:6d} {synth:6d}")

# Categories with lowest mean confidence
print("\n--- Categories with LOWEST avg confidence ---")
low_conf = []
for l3, confs in l3_confidence.items():
    avg = sum(confs) / len(confs) if confs else 0
    low_conf.append((l3, avg, len(confs)))

low_conf.sort(key=lambda x: x[1])
print(f"{'Category':<45} {'AvgConf':>8} {'Count':>7}")
for name, avg, count in low_conf[:20]:
    print(f"  {name:<43} {avg:7.3f} {count:6d}")

# L1-level imbalance
print("\n--- L1 Distribution (train) ---")
for l1, count in sorted(train_l1.items(), key=lambda x: -x[1]):
    test_count = test_l1.get(l1, 0)
    print(f"  {count:7d} train | {test_count:6d} test | {l1}")

# Summary for improvement strategy
print("\n--- IMPROVEMENT STRATEGY ---")
total_synth = sum(m.get('synthetic', 0) for m in l3_methods.values())
total_real = sum(sum(m.values()) - m.get('synthetic', 0) for m in l3_methods.values())
print(f"Real data: {total_real:,} ({total_real/(total_real+total_synth)*100:.1f}%)")
print(f"Synthetic data: {total_synth:,} ({total_synth/(total_real+total_synth)*100:.1f}%)")

# Categories that are entirely synthetic
all_synth = [name for name, methods in l3_methods.items() 
             if methods.get('synthetic', 0) == sum(methods.values())]
print(f"\nCategories with 100% synthetic data: {len(all_synth)}")
for name in sorted(all_synth)[:20]:
    total = sum(l3_methods[name].values())
    print(f"  {name} ({total} samples)")
