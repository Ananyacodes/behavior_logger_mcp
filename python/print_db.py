#!/usr/bin/env python3
"""Print database schema and rows; show newest 500 for large tables.

Usage: python print_db.py

Connects to the 'neurolock' database using credentials in this repo's scripts.
If a table has more than MAX_ROWS rows, tries to pick a sort column from a
priority list and prints the newest rows (ORDER BY sort_col DESC LIMIT MAX_ROWS).
"""
import mysql.connector
import sys

cfg = dict(host='localhost', port=3306, user='root', password='JoeMama@25', database='neurolock')
MAX_ROWS = 500
SORT_PRIORITY = [
    'created_at', 'processed_at', 'timestamp', 'stat_date',
    'id', 'event_id', 'alert_id', 'keystroke_id', 'mouse_id', 'metric_id', 'user_id'
]


def pick_sort_column(cols):
    names = [c[0] for c in cols]
    for s in SORT_PRIORITY:
        if s in names:
            return s
    # fallback to first column
    return names[0] if names else None


def print_table(cur, t):
    print('\n' + '='*80)
    print('Table:', t)
    cur.execute("SELECT COLUMN_NAME, DATA_TYPE, COLUMN_TYPE, IS_NULLABLE FROM information_schema.columns WHERE table_schema=%s AND table_name=%s ORDER BY ORDINAL_POSITION", (cfg['database'], t))
    cols = cur.fetchall()
    print('Columns:')
    for c in cols:
        print('  ', c)
    try:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        cnt = cur.fetchone()[0]
    except Exception as e:
        print('Row count: COUNT ERROR:', e)
        return
    print('Row count:', cnt)

    if cnt > MAX_ROWS:
        sort_col = pick_sort_column(cols)
        if sort_col:
            print(f"Table has {cnt} rows. Showing newest {MAX_ROWS} rows ordered by {sort_col} (DESC).")
            q = f"SELECT * FROM {t} ORDER BY {sort_col} DESC LIMIT %s"
            cur.execute(q, (MAX_ROWS,))
            rows = cur.fetchall()
            # reverse so we display newest last (chronological)
            rows = list(reversed(rows))
        else:
            print(f"Table has {cnt} rows and no suitable sort column was found; showing first {MAX_ROWS} rows.")
            cur.execute(f"SELECT * FROM {t} LIMIT %s", (MAX_ROWS,))
            rows = cur.fetchall()
    else:
        cur.execute(f"SELECT * FROM {t} LIMIT %s", (MAX_ROWS,))
        rows = cur.fetchall()

    if rows:
        header = [c[0] for c in cols]
        print(' | '.join(header))
        for r in rows:
            row_str = ' | '.join([str(x) if x is not None else 'NULL' for x in r])
            print(row_str)
    else:
        print('(no rows)')


def main():
    try:
        cnx = mysql.connector.connect(**cfg)
    except Exception as e:
        print('Error connecting to database:', e)
        sys.exit(1)
    cur = cnx.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s ORDER BY table_name", (cfg['database'],))
    tables = [r[0] for r in cur.fetchall()]
    print('Tables in', cfg['database'] + ':', ', '.join(tables))
    for t in tables:
        print_table(cur, t)
    cnx.close()


if __name__ == '__main__':
    main()
