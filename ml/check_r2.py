import csv

rows = list(csv.DictReader(open("ml/models/v5_round2_finetune/training_log.csv")))
print(f"Total epochs: {len(rows)}")
best_ep = 0
best_v = 0.0
for r in rows:
    ep = int(r["epoch"])
    val = float(r["val_L3_probs_accuracy"])
    trn = float(r["L3_probs_accuracy"])
    print(f"  Epoch {ep}: val_L3={val:.4f}  train_L3={trn:.4f}")
    if val > best_v:
        best_v = val
        best_ep = ep

print(f"\nBest: epoch {best_ep} val_L3={best_v:.4f}")
print(f"Epochs since best: {len(rows)-1 - best_ep}")
print(f"Patience=10, will early stop at epoch {best_ep + 10}")
