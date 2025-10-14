import mysql.connector

DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'database': 'neurolock',
    'user': 'root',
    'password': 'JoeMama@25'
}

tables = [
    'alerts', 'anomaly_stats', 'application_events',
    'keystroke_events', 'mouse_events', 'system_metrics', 'users'
]

conn = mysql.connector.connect(**DB_CONFIG)
cur = conn.cursor()

for t in tables:
    cur.execute("SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s", (DB_CONFIG['database'], t))
    rows = cur.fetchall()
    print(f"\nTable: {t}")
    if not rows:
        print('  (table not found)')
    else:
        for col, dt in rows:
            print(f"  {col} ({dt})")

cur.close()
conn.close()
