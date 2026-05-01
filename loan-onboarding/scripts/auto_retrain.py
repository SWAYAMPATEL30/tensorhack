#!/usr/bin/env python3
"""
Auto-Retrain Script — Poonawalla Fincorp Loan Wizard
Runs daily to check for new data and retrain models if needed.
Usage: python scripts/auto_retrain.py
"""
import os, time, csv, glob
from datetime import datetime
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score

BASE          = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR      = os.path.join(BASE, "data")
INCOMING_DIR  = os.path.join(DATA_DIR, "incoming")
MODEL_DIR     = os.path.join(BASE, "models")
LOG_PATH      = os.path.join(BASE, "reports", "retrain_log.csv")

MIN_NEW_ROWS         = 500
IMPROVEMENT_THRESH   = 0.01   # 1% AUC improvement to auto-promote

os.makedirs(INCOMING_DIR, exist_ok=True)

def log_run(model_name, old_auc, new_auc, promoted, rows):
    file_exists = os.path.exists(LOG_PATH)
    with open(LOG_PATH, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["timestamp","model","old_auc","new_auc","promoted","new_rows"])
        if not file_exists: w.writeheader()
        w.writerow({
            "timestamp": datetime.now().isoformat(),
            "model": model_name,
            "old_auc": f"{old_auc:.4f}",
            "new_auc": f"{new_auc:.4f}",
            "promoted": promoted,
            "new_rows": rows
        })
    print(f"  [LOG] {model_name}: old={old_auc:.4f} new={new_auc:.4f} promoted={promoted}")

def check_and_retrain():
    incoming_files = glob.glob(os.path.join(INCOMING_DIR, "credit_risk_*.csv"))
    if not incoming_files:
        print(f"[{datetime.now():%H:%M:%S}] No new data found in {INCOMING_DIR}")
        return

    new_dfs = [pd.read_csv(f) for f in incoming_files]
    new_df = pd.concat(new_dfs, ignore_index=True)
    if len(new_df) < MIN_NEW_ROWS:
        print(f"  Only {len(new_df)} new rows — minimum is {MIN_NEW_ROWS}. Skipping.")
        return

    print(f"  Found {len(new_df)} new rows. Loading existing data...")
    existing = pd.read_csv(os.path.join(DATA_DIR, "credit_risk_train.csv"))
    combined = pd.concat([existing, new_df], ignore_index=True).drop_duplicates()

    # Load production model
    prod_bundle = joblib.load(os.path.join(MODEL_DIR, "credit_risk_xgb.pkl"))
    prod_model = prod_bundle["model"]
    le = prod_bundle["label_encoder"]
    feat_cols = prod_bundle["feature_cols"]

    combined["employment_type"] = le.transform(combined["employment_type"])
    X = combined[feat_cols]
    y = combined["default_label"]

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.15,
                                                stratify=y, random_state=42)
    prod_auc = roc_auc_score(y_te, prod_model.predict_proba(X_te)[:, 1])

    # Simple retrain
    import xgboost as xgb
    scale_pos = (y_tr==0).sum()/(y_tr==1).sum()
    new_model = xgb.XGBClassifier(
        n_estimators=300, max_depth=5, learning_rate=0.08,
        scale_pos_weight=scale_pos, seed=42,
        verbosity=0, use_label_encoder=False
    )
    new_model.fit(X_tr, y_tr)
    new_auc = roc_auc_score(y_te, new_model.predict_proba(X_te)[:, 1])

    promoted = False
    if new_auc - prod_auc >= IMPROVEMENT_THRESH:
        prod_bundle["model"] = new_model
        joblib.dump(prod_bundle, os.path.join(MODEL_DIR, "credit_risk_xgb.pkl"))
        # Archive old data
        combined.to_csv(os.path.join(DATA_DIR, "credit_risk_train.csv"), index=False)
        # Move incoming files to processed
        for f in incoming_files:
            os.rename(f, f + ".processed")
        promoted = True
        print(f"  ✅ Model promoted! AUC improved {prod_auc:.4f} → {new_auc:.4f}")
    else:
        print(f"  ℹ️  No improvement ({prod_auc:.4f} → {new_auc:.4f}). Keeping production model.")

    log_run("credit_risk_xgb", prod_auc, new_auc, promoted, len(new_df))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval-hours", type=int, default=24)
    args = parser.parse_args()

    print(f"Auto-Retrain Agent started. Check interval: {args.interval_hours}h")
    while True:
        print(f"\n[{datetime.now():%Y-%m-%d %H:%M:%S}] Running retrain check...")
        try:
            check_and_retrain()
        except Exception as e:
            print(f"  ERROR: {e}")
        time.sleep(args.interval_hours * 3600)
