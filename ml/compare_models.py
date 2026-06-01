import json, os

models_dir = "ml/models"
for d in sorted(os.listdir(models_dir)):
    report_path = os.path.join(models_dir, d, "evaluation_report.json")
    if os.path.exists(report_path):
        with open(report_path) as f:
            r = json.load(f)
        l1 = r.get("L1_top1_accuracy", "?")
        l2 = r.get("L2_top1_accuracy", "?")
        l3 = r.get("L3_top1_accuracy", "?")
        t3 = r.get("L3_top3_accuracy", "?")
        t5 = r.get("L3_top5_accuracy", "?")
        hc = r.get("hierarchy_L3_L1_consistency", "?")
        gd = r.get("hierarchy_graceful_degradation", "?")
        params = r.get("total_params", "?")
        tflite = r.get("tflite_size_mb", "?")
        print(f"\n=== {d} ===")
        print(f"  L1={l1}  L2={l2}  L3={l3}  Top3={t3}  Top5={t5}")
        print(f"  HC_L1={hc}  Graceful={gd}")
        print(f"  Params={params}  TFLite={tflite}MB")
