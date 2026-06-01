import csv, os

logs = [
    ('R1', 'ml/models/v5_round1_3layer/training_log.csv'),
    ('R2', 'ml/models/v5_round2_finetune/training_log.csv'),
]
for name, path in logs:
    try:
        with open(path, 'r') as f:
            rows = list(csv.DictReader(f))
        if not rows:
            print(f"{name}: empty log")
            continue
        col = None
        for c in ['val_L3_probs_accuracy', 'val_l3_accuracy']:
            if c in rows[0]:
                col = c
                break
        if col:
            best_row = max(rows, key=lambda r: float(r[col]))
            best_l3 = float(best_row[col])
            best_ep = best_row.get('epoch', '?')
            last = rows[-1]
            last_l3 = float(last[col])
            last_ep = last.get('epoch', '?')
            
            # Also get L1, L2, Top3
            l1_col = col.replace('L3', 'L1')
            l2_col = col.replace('L3', 'L2')
            t3_col = None
            for c2 in ['val_L3_probs_top3_acc', 'val_l3_top3_acc']:
                if c2 in rows[0]:
                    t3_col = c2
                    break
            
            best_l1 = float(best_row.get(l1_col, 0))
            best_l2 = float(best_row.get(l2_col, 0))
            best_t3 = float(best_row.get(t3_col, 0)) if t3_col else 0
            
            print(f"=== {name}: {len(rows)} epochs ===")
            print(f"  Best epoch {best_ep}: L1={best_l1:.4f} L2={best_l2:.4f} L3={best_l3:.4f} Top3={best_t3:.4f}")
            print(f"  Last epoch {last_ep}: L3={last_l3:.4f}")
            
            # Show last 5 epochs
            print(f"  Recent:")
            for r in rows[-5:]:
                ep = r.get('epoch', '?')
                vl3 = float(r[col])
                vt3 = float(r.get(t3_col, 0)) if t3_col else 0
                print(f"    ep {ep}: val_L3={vl3:.4f} val_Top3={vt3:.4f}")
        else:
            print(f"{name}: {len(rows)} epochs, cols={list(rows[0].keys())[:8]}")
    except Exception as e:
        print(f"{name}: error - {e}")

# Check if background training is still running
import subprocess
result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], capture_output=True, text=True)
python_procs = [l for l in result.stdout.split('\n') if 'python' in l.lower()]
print(f"\nActive python processes: {len(python_procs)}")
for p in python_procs:
    print(f"  {p.strip()}")
