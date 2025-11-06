#!/usr/bin/env python3
"""
Ensure specific columns exist on behavior_logs table; add them if missing.
This is compatible with MySQL versions that don't support ADD COLUMN IF NOT EXISTS.
"""
import mysql.connector
import os

DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'database': 'neurolock',
    'user': 'root',
    'password': 'JoeMama@25',
}

COLUMNS = {
    'anomaly_score': 'DOUBLE NULL',
    'detector': "VARCHAR(64) NULL",
    'model_version': "VARCHAR(32) NULL",
    'detected_by': "VARCHAR(32) NULL",
}


def connect():
    return mysql.connector.connect(**DB_CONFIG)


def column_exists(cur, table, column):
    cur.execute("""
        SELECT COUNT(*) FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = %s
    """, (DB_CONFIG['database'], table, column))
    return cur.fetchone()[0] > 0


def main():
    conn = connect()
    cur = conn.cursor()
    for col, definition in COLUMNS.items():
        if column_exists(cur, 'behavior_logs', col):
            print(f"Column {col} already exists")
            continue
        stmt = f"ALTER TABLE behavior_logs ADD COLUMN {col} {definition}"
        try:
            print('Executing:', stmt)
            cur.execute(stmt)
        except Exception as e:
            print('Failed to add column', col, e)
    conn.commit()
    cur.close(); conn.close()
    print('ensure_columns complete')

if __name__ == '__main__':
    main()
