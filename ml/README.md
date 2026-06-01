# Xpenzo ML Pipeline

Train → Export → Deploy the CHT (Compact Hierarchical Transformer) model that classifies Indian UPI transactions into 15 → 80 → 520 categories, 100% on-device, under 5 MB.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate synthetic training data
python generate_data.py --output data/train.csv --n_samples 200000
python generate_data.py --output data/val.csv   --n_samples 20000 --seed 99

# 3. Train the SentencePiece tokenizer
python train_cht.py --mode train_tokenizer --data data/train.csv

# 4. Train the CHT model
python train_cht.py --mode train --data data/train.csv --val data/val.csv

# 5. Export to TFLite (INT8 quantized)
python train_cht.py --mode export --checkpoint outputs/cht_best.keras
```

Output files to copy into Android assets/:
- `outputs/xpenz_cht_v3.tflite`   (~3.2 MB)
- `outputs/xpenz_bpe.model`        (~150 KB)
- `outputs/label_encoders.pkl`     (needed to generate labels_l1/l2/l3.txt)

## How to Swap Models in Android

`ModelManager` is the single place to change the active model. No app restart needed:

```kotlin
// Get the singleton
val manager = ModelManager.getInstance(context)

// Switch to rule engine only (for debugging)
manager.switchModel("rule_engine")

// Switch back to full ensemble
manager.switchModel("ensemble")

// Register and activate your own custom model
val myModel = MyNewClassifier(context)
manager.registerModel("my_v4", myModel)
manager.switchModel("my_v4")
```

## Architecture

```
TransactionClassifier (interface)
       │
       ├── EnsembleClassifier  ← DEFAULT (all 4 components)
       │       ├── CHTClassifier     (TFLite, ~3.2 MB, ~30ms)
       │       ├── RuleEngine        (deterministic, ~50 KB)
       │       ├── HabitModel        (per-user cache)
       │       └── AmountTimePrior   (statistical lookup)
       │
       ├── CHTClassifier       ← neural only
       ├── RuleEngine          ← rules only (no ML)
       └── HabitModel          ← user history only
```

## Ensemble Weights (auto-adapts)

| User stage       | CHT | Rules | ATP | Habit |
|------------------|-----|-------|-----|-------|
| Cold-start (0)   | 60% |  25%  | 15% |   0%  |
| Warm (10-50 txn) | 45% |  15%  | 10% |  30%  |
| Mature (50+ txn) | 35% |  10%  |  5% |  50%  |
