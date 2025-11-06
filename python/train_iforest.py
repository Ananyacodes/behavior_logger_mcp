#!/usr/bin/env python3
"""
Train a simple IsolationForest anomaly detector on available numeric fields in `behavior_logs`.
This script extracts simple features from `raw_data` JSON (cpu_percent, memory_percent, raw_length)
and trains a StandardScaler + IsolationForest. It saves the artifacts to `python/models/`.

Usage: python python/train_iforest.py --limit 10000
"""
import mysql.connector
import os
import json
import argparse
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from joblib import dump

DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'database': 'neurolock',
    'user': 'root',
    'password': 'JoeMama@25',
}

MODELS_DIR = os.path.join(os.path.dirname(__file__), 'models')
IF_MODEL_PATH = os.path.join(MODELS_DIR, 'if_model_v1.joblib')
IF_SCALER_PATH = os.path.join(MODELS_DIR, 'if_scaler_v1.joblib')

os.makedirs(MODELS_DIR, exist_ok=True)


def extract_features_from_raw(raw):
    try:
        if raw is None:
            return [0.0, 0.0, 0.0]
        if isinstance(raw, str):
            rd = json.loads(raw)
        elif isinstance(raw, dict):
            rd = raw
        else:
            return [0.0, 0.0, 0.0]
        cpu = float(rd.get('cpu_percent', 0) or 0)
        mem = float(rd.get('memory_percent', 0) or 0)
        length = float(len(json.dumps(rd)))
        return [cpu, mem, length]
    except Exception:
        return [0.0, 0.0, 0.0]


def fetch_rows(limit=10000):
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT id, event_type, raw_data FROM behavior_logs WHERE raw_data IS NOT NULL LIMIT %s", (limit,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=5000)
    args = parser.parse_args()

    print(f"Fetching up to {args.limit} rows from DB...")
    rows = fetch_rows(limit=args.limit)
    if not rows:
        print("No rows found. Insert some events before training or provide a feature CSV.")
        return

    X = []
    for r in rows:
        _, event_type, raw = r
        feats = extract_features_from_raw(raw)
        # add simple event_type encoding as extra feature (map unknown to 0)
        type_code = 0.0
        if event_type:
            # map common types
            et = str(event_type).upper()
            if 'SYSTEM' in et:
                type_code = 1.0
            elif 'KEY' in et or 'KEYSTROKE' in et:
                type_code = 2.0
            elif 'MOUSE' in et:
                type_code = 3.0
            else:
                type_code = 0.0
        feats.append(type_code)
        X.append(feats)

    X = np.array(X, dtype=float)
    print("Feature shape:", X.shape)

    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    print("Training IsolationForest...")
    clf = IsolationForest(n_estimators=200, max_samples='auto', contamination=0.01, random_state=42)
    clf.fit(Xs)

    dump(scaler, IF_SCALER_PATH)
    dump(clf, IF_MODEL_PATH)
    print(f"Saved scaler to: {IF_SCALER_PATH}")
    print(f"Saved model to: {IF_MODEL_PATH}")

if __name__ == '__main__':
    main()
