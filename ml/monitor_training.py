#!/usr/bin/env python3
"""Monitor all model training directories for status — v2."""
import json, time
from pathlib import Path

MODELS_DIR = Path(__file__).parent / "models"

print(f"\n{'='*70}")
print(f"  MODEL STATUS — {time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*70}\n")

for d in sorted(MODELS_DIR.iterdir()):
    if not d.is_dir():
        continue
    log = d / "training_log.csv"
    report = d / "evaluation_report.json"
    
    if report.exists():
        r = json.loads(report.read_text())
        l3 = r.get('L3_top1_accuracy', 0)
        t3 = r.get('L3_top3_accuracy', 0)
        hc = r.get('hierarchy_consistency', 0)
        print(f"  [{d.name}] COMPLETE — L3={l3:.4f} Top3={t3:.4f} HC={hc:.4f}")
        tfl = d / "model.tflite"
        if tfl.exists():
            print(f"    TFLite: {tfl.stat().st_size/1024/1024:.2f} MB")
        print()
        continue
    
    if log.exists():
        lines = log.read_text().strip().split("\n")
        if len(lines) > 1:
            header = lines[0].split(",")
            epochs = len(lines) - 1
            vi = next((i for i, c in enumerate(header) if "val_L3" in c and "accuracy" in c and "top" not in c), None)
            if vi is not None:
                vals = [float(l.split(",")[vi]) for l in lines[1:] if l.strip()]
                best = max(vals)
                latest = vals[-1]
                active = " >>> TRAINING <<<" if time.time() - log.stat().st_mtime < 120 else ""
                print(f"  [{d.name}] {epochs} epochs | best L3={best:.4f} | latest={latest:.4f}{active}\n")
            else:
                print(f"  [{d.name}] {epochs} epochs (no L3 accuracy col)\n")
        else:
            print(f"  [{d.name}] empty log\n")
    elif (d / "best.keras").exists():
        sz = (d / "best.keras").stat().st_size / 1024 / 1024
        print(f"  [{d.name}] best.keras={sz:.1f}MB (no log)\n")
    else:
        print(f"  [{d.name}] no artifacts\n")
