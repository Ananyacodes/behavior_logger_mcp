#!/usr/bin/env python3
"""
One-shot inference runner using the trained IsolationForest artifacts produced by train_iforest.py.
Connects to MySQL, selects up to 100 unprocessed rows from behavior_logs, scores them using the
scaler+iforest, writes prediction, anomaly_score, detector, model_version, detected_by, processed_at,
and clears hashed_event to NULL (preserving raw_data).

Usage: python python/run_infer_once.py
"""
import os
import sys
import json
from datetime import datetime

try:
    from joblib import load
    HAS_JOBLIB = True
except Exception:
    HAS_JOBLIB = False

import mysql.connector
import numpy as np
from math import exp

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

MODEL_VERSION = os.path.splitext(os.path.basename(IF_MODEL_PATH))[0]


def connect():
    return mysql.connector.connect(**DB_CONFIG)


def load_artifacts():
    if not HAS_JOBLIB:
        print('joblib not available in this environment')
        return None, None
    if not (os.path.exists(IF_MODEL_PATH) and os.path.exists(IF_SCALER_PATH)):
        print('IsolationForest artifacts not found in', MODELS_DIR)
        return None, None
    clf = load(IF_MODEL_PATH)
    scaler = load(IF_SCALER_PATH)
    print('Loaded classifier and scaler from', MODELS_DIR)
    return clf, scaler


def extract_features(raw_data, event_type):
    try:
        if raw_data is None:
            rd = {}
        elif isinstance(raw_data, str):
            rd = json.loads(raw_data)
        elif isinstance(raw_data, dict):
            rd = raw_data
        else:
            rd = {}
    except Exception:
        rd = {}
    cpu = float(rd.get('cpu_percent', 0) or 0)
    mem = float(rd.get('memory_percent', 0) or 0)
    length = float(len(json.dumps(rd))) if rd is not None else 0.0
    type_code = 0.0
    if event_type:
        et = str(event_type).upper()
        if 'SYSTEM' in et:
            type_code = 1.0
        elif 'KEY' in et or 'KEYSTROKE' in et:
            type_code = 2.0
        elif 'MOUSE' in et:
            type_code = 3.0
    return [cpu, mem, length, type_code]


def logistic(x):
    return 1.0 / (1.0 + exp(-x))


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--rescore', action='store_true', help='Rescore rows where anomaly_score IS NULL')
    parser.add_argument('--limit', type=int, default=100, help='Maximum rows to process in one batch')
    args = parser.parse_args()

    clf, scaler = load_artifacts()
    if clf is None or scaler is None:
        print('No model artifacts available - aborting one-shot inference')
        return

    conn = connect()
    cur = conn.cursor()
    if args.rescore:
        # Rescore rows that have prediction set (or not) but missing anomaly_score
        print(f'Rescoring up to {args.limit} rows with NULL anomaly_score...')
        cur.execute("""
            SELECT id, timestamp, event_type, hashed_event, raw_data
            FROM behavior_logs
            WHERE (anomaly_score IS NULL) AND (raw_data IS NOT NULL OR hashed_event IS NOT NULL)
            ORDER BY timestamp ASC
            LIMIT %s
        """, (args.limit,))
    else:
        cur.execute("""
            SELECT id, timestamp, event_type, hashed_event, raw_data
            FROM behavior_logs
            WHERE prediction IS NULL AND hashed_event IS NOT NULL
            ORDER BY timestamp ASC
            LIMIT %s
        """, (args.limit,))
    rows = cur.fetchall()
    if not rows:
        print('No unprocessed rows found')
        cur.close(); conn.close(); return

    total = 0
    anomalies = 0
    conf_sum = 0.0

    for row in rows:
        row_id, timestamp, event_type, hashed_event, raw_data = row
        feats = extract_features(raw_data, event_type)
        X = np.array([feats], dtype=float)
        Xs = scaler.transform(X)
        try:
            raw_score = -float(clf.decision_function(Xs)[0])
        except Exception:
            raw_score = -float(clf.score_samples(Xs)[0])
        anomaly_score = logistic(raw_score)
        prediction = 1 if anomaly_score >= 0.5 else 0
        detector = 'IsolationForest'
        detected_by = 'model'
        model_version = MODEL_VERSION

        # persist
        if args.rescore:
            # For rescoring, do not clear hashed_event and preserve existing prediction if present
            cur.execute("""
                UPDATE behavior_logs
                SET prediction = %s,
                    anomaly_score = %s,
                    detector = %s,
                    model_version = %s,
                    detected_by = %s,
                    processed_at = NOW()
                WHERE id = %s
            """, (prediction, float(anomaly_score), detector, model_version, detected_by, row_id))
        else:
            cur.execute("""
                UPDATE behavior_logs
                SET prediction = %s,
                    anomaly_score = %s,
                    detector = %s,
                    model_version = %s,
                    detected_by = %s,
                    processed_at = NOW(),
                    hashed_event = NULL
                WHERE id = %s
            """, (prediction, float(anomaly_score), detector, model_version, detected_by, row_id))

        total += 1
        if prediction == 1:
            anomalies += 1
        conf_sum += float(anomaly_score)
        print(f'Processed id={row_id} -> pred={prediction} score={anomaly_score:.4f}')

    conn.commit()
    cur.close()
    conn.close()

    avg_conf = conf_sum / total if total else 0.0
    print(f'Batch processed: total={total} anomalies={anomalies} avg_score={avg_conf:.4f}')

    # write a simple anomaly_stats row for this window
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO anomaly_stats (window_start, window_end, total_events, anomalies, avg_anomaly_score)
            VALUES (NOW(), NOW(), %s, %s, %s)
        """, (total, anomalies, avg_conf))
        conn.commit()
        cur.close(); conn.close()
        print('Wrote anomaly_stats entry')
    except Exception as e:
        print('Failed to write anomaly_stats:', e)

if __name__ == '__main__':
    main()
