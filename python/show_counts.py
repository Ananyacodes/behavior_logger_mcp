import mysql.connector

DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'database': 'neurolock',
    'user': 'root',
    'password': 'JoeMama@25'
}

tables = ['behavior_logs','alerts','anomaly_stats','application_events','keystroke_events','mouse_events','system_metrics','users']

cn = mysql.connector.connect(**DB_CONFIG)
cur = cn.cursor()
for t in tables:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        print(f"{t}: {cur.fetchone()[0]}")
    except Exception as e:
        print(f"{t}: ERROR - {e}")
cur.close()
cn.close()
