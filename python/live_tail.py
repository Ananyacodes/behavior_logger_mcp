import time
import mysql.connector
from datetime import datetime

cfg = dict(host='localhost', port=3306, user='root', password='JoeMama@25', database='neurolock')

def tail_behavior_logs(poll_interval=1.0):
    conn = mysql.connector.connect(**cfg)
    cur = conn.cursor()

    # Initialize last seen id
    cur.execute("SELECT COALESCE(MAX(id), 0) FROM behavior_logs")
    last_id = cur.fetchone()[0]
    print(f"Starting live tail. Last seen id={last_id}")

    try:
        while True:
            cur.execute("SELECT id, timestamp, event_type, raw_data FROM behavior_logs WHERE id > %s ORDER BY id ASC", (last_id,))
            rows = cur.fetchall()
            for r in rows:
                _id, ts, etype, raw = r
                # Normalize timestamp
                try:
                    ts_disp = datetime.fromtimestamp(float(ts)).isoformat()
                except Exception:
                    ts_disp = str(ts)
                print(f"[{_id}] {ts_disp} | {etype} | {raw}")
                last_id = _id
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        print("Stopping live tail")
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    tail_behavior_logs()
