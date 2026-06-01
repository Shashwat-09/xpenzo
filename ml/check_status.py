"""Quick training status check"""
import csv, os, json

log_dirs = ['ml/models/v4_overnight_r1', 'ml/models/v4_round1_3layer', 'ml/models/quick_test']
for d in log_dirs:
    log = os.path.join(d, 'training_log.csv')
    if os.path.exists(log):
        with open(log, 'r') as f:
            rows = list(csv.DictReader(f))
            if rows:
                last = rows[-1]
                # Try different column name patterns
                l3_col = None
                for col in ['val_L3_probs_accuracy', 'val_l3_accuracy', 'val_L3_accuracy']:
                    if col in last:
                        l3_col = col
                        break
                if l3_col:
                    best_l3 = max(float(r[l3_col]) for r in rows)
                    last_l3 = float(last[l3_col])
                    print(f"{d}: {len(rows)} epochs, last_L3={last_l3:.4f}, best_L3={best_l3:.4f}")
                else:
                    print(f"{d}: {len(rows)} epochs (columns: {list(last.keys())[:5]}...)")
            else:
                print(f"{d}: empty log")
    else:
        print(f"{d}: no log found")
    
    best_path = os.path.join(d, 'best.keras')
    if os.path.exists(best_path):
        size_mb = os.path.getsize(best_path) / 1024 / 1024
        print(f"  -> best.keras: {size_mb:.1f} MB")

# Check combined dataset stats
train_csv = 'ml/training/train.csv'
if os.path.exists(train_csv):
    with open(train_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = sum(1 for _ in reader)
    print(f"\nTraining data: {count} rows")
