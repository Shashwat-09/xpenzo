#!/usr/bin/env python3
"""Quick check of v4 training progress across all rounds."""
from __future__ import annotations

import csv
import json
from pathlib import Path

MODELS_DIR = Path(__file__).resolve().parent / "models"

ROUNDS = [
    "v4_round1_3layer",
    "v4_round2_finetune",
    "v4_round3_4layer",
    "v4_round4_4layer_finetune",
]

V3_BASELINE = {"L1": 81.9, "L2": 73.3, "L3": 68.8, "Top3": 83.0, "Top5": 86.5, "HC": 48.6}


def check_round(name: str) -> None:
    rdir = MODELS_DIR / name
    log = rdir / "training_log.csv"
    report = rdir / "evaluation_report.json"

    if not rdir.exists():
        print(f"  {name:35s} | Not started yet")
        return

    if report.exists():
        with open(report, encoding="utf-8") as f:
            r = json.load(f)
        l1 = r.get("L1_top1_accuracy", 0) * 100
        l2 = r.get("L2_top1_accuracy", 0) * 100
        l3 = r.get("L3_top1_accuracy", 0) * 100
        t3 = r.get("L3_top3_accuracy", 0) * 100
        hc = r.get("hierarchy_L3_L1_consistency", 0) * 100
        ep = r.get("epochs_trained", "?")
        mins = r.get("training_time_min", 0)
        tflite = r.get("tflite_size_mb", 0)
        print(f"  {name:35s} | DONE {ep}ep {mins:.0f}min | L1={l1:.1f}% L2={l2:.1f}% L3={l3:.1f}% Top3={t3:.1f}% HC={hc:.1f}% | TFLite={tflite:.2f}MB")
        return

    if not log.exists():
        print(f"  {name:35s} | Directory exists but no log yet")
        return

    with open(log, encoding="utf-8") as f:
        content = f.read().strip()
    if not content:
        print(f"  {name:35s} | Log file is empty")
        return
    reader = list(csv.DictReader(content.splitlines()))

    if not reader:
        print(f"  {name:35s} | Log exists but 0 epochs logged")
        return

    n = len(reader)
    last = reader[-1]
    best_l3 = max(float(row.get("val_L3_probs_accuracy", 0)) for row in reader)
    l1 = float(last.get("val_L1_probs_accuracy", 0)) * 100
    l2 = float(last.get("val_L2_probs_accuracy", 0)) * 100
    l3 = float(last.get("val_L3_probs_accuracy", 0)) * 100
    t3 = float(last.get("val_L3_probs_top3_acc", 0)) * 100
    loss = float(last.get("val_loss", 0))
    print(f"  {name:35s} | {n} epochs done | L1={l1:.1f}% L2={l2:.1f}% L3={l3:.1f}% Top3={t3:.1f}% loss={loss:.4f} | best_L3={best_l3*100:.1f}%")


def main() -> None:
    print("=" * 90)
    print("  XPENZO CHT v4 TRAINING PROGRESS")
    print("=" * 90)
    print(f"\n  v3 Baseline: L1={V3_BASELINE['L1']}% L2={V3_BASELINE['L2']}% L3={V3_BASELINE['L3']}% Top3={V3_BASELINE['Top3']}% HC={V3_BASELINE['HC']}%\n")

    # Quick test
    qt = MODELS_DIR / "quick_test"
    if qt.exists():
        check_round("quick_test")
        print()

    for name in ROUNDS:
        check_round(name)

    # Check for champion
    champion = MODELS_DIR / "xpenz_cht_v4.keras"
    if champion.exists():
        print(f"\n  CHAMPION MODEL: {champion} EXISTS")
        ev = MODELS_DIR / "evaluation_report_v4.json"
        if ev.exists():
            with open(ev, encoding="utf-8") as f:
                r = json.load(f)
            print(f"  Champion: L3={r.get('L3_top1_accuracy',0)*100:.1f}% Top3={r.get('L3_top3_accuracy',0)*100:.1f}%")

    print("\n" + "=" * 90)


if __name__ == "__main__":
    main()
