import mysql.connector

DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'database': 'neurolock',
    'user': 'root',
    'password': 'JoeMama@25'
}

conn = mysql.connector.connect(**DB_CONFIG)
cur = conn.cursor()

def print_columns(table):
    print(f"Schema for {table}:")
    cur.execute(f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s", (DB_CONFIG['database'], table))
    rows = cur.fetchall()
    if not rows:
        print("  (table not found)")
    else:
        for col, dt in rows:
            print(f"  {col} ({dt})")
    print()

print_columns('behavior_logs')
print_columns('anomaly_stats')

cur.close()
conn.close()
