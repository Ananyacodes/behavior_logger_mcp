#!/usr/bin/env python3
"""
Run SQL migration to add ML/anomaly columns to behavior_logs and create anomaly_stats.
This script connects to MySQL using credentials below and executes the SQL statements in
sql/migrations/0001_add_ml_columns.sql.
"""
import mysql.connector
import os
import sys

DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'database': 'neurolock',
    'user': 'root',
    'password': 'JoeMama@25',
}

SQL_FILE = os.path.join(os.path.dirname(__file__), '..', 'sql', 'migrations', '0001_add_ml_columns.sql')


def load_sql(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Remove single-line comments
    lines = []
    for ln in content.splitlines():
        if ln.strip().startswith('--'):
            continue
        lines.append(ln)
    content = '\n'.join(lines)
    # Split on semicolon; keep statements that contain non-whitespace
    stmts = [s.strip() for s in content.split(';') if s.strip()]
    return stmts


def main():
    if not os.path.exists(SQL_FILE):
        print(f"Migration SQL not found: {SQL_FILE}")
        sys.exit(1)

    stmts = load_sql(SQL_FILE)
    print(f"Loaded {len(stmts)} SQL statements from migration file")

    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()
    for s in stmts:
        try:
            print('Executing:', s[:120].replace('\n',' '))
            cur.execute(s)
        except Exception as e:
            print('Warning: statement failed:', e)
    conn.commit()
    cur.close()
    conn.close()
    print('Migration complete')

if __name__ == '__main__':
    main()
