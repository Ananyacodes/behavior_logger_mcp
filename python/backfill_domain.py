"""
Backfill domain tables from already-processed behavior_logs.
Run with the project's virtualenv Python:
  C:/Users/Ananya/behavior_logger/.venv/Scripts/python.exe backfill_domain.py
"""
import json
import mysql.connector

DB = dict(host='localhost', port=3306, database='neurolock', user='root', password='JoeMama@25')

BATCH = 1000

def get_conn():
    return mysql.connector.connect(**DB)


def backfill():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)

    # Select processed logs that may not have domain inserts
    cur.execute("""
        SELECT id, timestamp, event_type, raw_data, prediction
        FROM behavior_logs
        WHERE (prediction IS NOT NULL OR processed_at IS NOT NULL)
        ORDER BY id ASC
        LIMIT %s
    """, (BATCH,))

    rows = cur.fetchall()
    if not rows:
        print("No processed rows to backfill.")
        cur.close(); conn.close(); return

    print(f"Backfilling {len(rows)} processed behavior_logs...")

    ins_keystroke = conn.cursor()
    ins_mouse = conn.cursor()
    ins_app = conn.cursor()
    ins_system = conn.cursor()
    ins_alert = conn.cursor()
    chk = conn.cursor()

    for r in rows:
        rid = r['id']
        ev = r.get('event_type') or ''
        raw = r.get('raw_data')
        pred = r.get('prediction')

        parsed = None
        if raw:
            try:
                parsed = json.loads(raw)
            except Exception:
                parsed = None

        ev_up = ev.upper()

        # keystroke
        if 'KEY' in ev_up:
            # check exists
            chk.execute("SELECT 1 FROM keystroke_events WHERE event_id=%s LIMIT 1", (rid,))
            if chk.fetchone() is None:
                key_name = None
                key_type = None
                interval_ms = None
                if isinstance(parsed, dict):
                    key_name = parsed.get('key') or parsed.get('key_name') or parsed.get('keyCode')
                    key_type = parsed.get('type') or parsed.get('key_type')
                    interval_ms = parsed.get('interval_ms') or parsed.get('interval')
                if key_name is None:
                    key_name = raw
                try:
                    ins_keystroke.execute(
                        "INSERT INTO keystroke_events (event_id, key_name, key_type, interval_ms) VALUES (%s, %s, %s, %s)",
                        (rid, key_name, key_type, interval_ms)
                    )
                except Exception as e:
                    print(f"keystroke insert failed for {rid}: {e}")

        # mouse
        if 'MOUSE' in ev_up:
            chk.execute("SELECT 1 FROM mouse_events WHERE event_id=%s LIMIT 1", (rid,))
            if chk.fetchone() is None:
                x = parsed.get('x') if isinstance(parsed, dict) else None
                y = parsed.get('y') if isinstance(parsed, dict) else None
                action = parsed.get('action') if isinstance(parsed, dict) else None
                button = parsed.get('button') if isinstance(parsed, dict) else None
                velocity = parsed.get('velocity') if isinstance(parsed, dict) else None
                screen_region = parsed.get('screen_region') if isinstance(parsed, dict) else None
                try:
                    ins_mouse.execute(
                        "INSERT INTO mouse_events (event_id, x_position, y_position, action, button, velocity, screen_region) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (rid, x, y, action, button, velocity, screen_region)
                    )
                except Exception as e:
                    print(f"mouse insert failed for {rid}: {e}")

        # application
        if 'APP' in ev_up:
            chk.execute("SELECT 1 FROM application_events WHERE event_id=%s LIMIT 1", (rid,))
            if chk.fetchone() is None:
                app_name = parsed.get('name') if isinstance(parsed, dict) else None
                window_title = parsed.get('title') if isinstance(parsed, dict) else None
                process_id = parsed.get('pid') if isinstance(parsed, dict) else None
                cpu = parsed.get('cpu_percent') if isinstance(parsed, dict) else None
                mem = parsed.get('memory_percent') if isinstance(parsed, dict) else None
                thr = parsed.get('num_threads') if isinstance(parsed, dict) else None
                try:
                    ins_app.execute(
                        "INSERT INTO application_events (event_id, app_name, window_title, process_id, cpu_percent, memory_percent, thread_count) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (rid, app_name, window_title, process_id, cpu, mem, thr)
                    )
                except Exception as e:
                    print(f"app insert failed for {rid}: {e}")

        # system
        if 'SYSTEM' in ev_up:
            chk.execute("SELECT 1 FROM system_metrics WHERE event_id=%s LIMIT 1", (rid,))
            if chk.fetchone() is None:
                cpu = parsed.get('cpu_percent') if isinstance(parsed, dict) else None
                mem = parsed.get('memory_percent') if isinstance(parsed, dict) else None
                mem_avail = parsed.get('memory_available_gb') if isinstance(parsed, dict) else None
                disk_free = parsed.get('disk_free_gb') if isinstance(parsed, dict) else None
                net_sent = parsed.get('network_bytes_sent') if isinstance(parsed, dict) else None
                net_recv = parsed.get('network_bytes_recv') if isinstance(parsed, dict) else None
                try:
                    ins_system.execute(
                        "INSERT INTO system_metrics (event_id, cpu_percent, memory_percent, memory_available_gb, disk_free_gb, network_bytes_sent, network_bytes_recv) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (rid, cpu, mem, mem_avail, disk_free, net_sent, net_recv)
                    )
                except Exception as e:
                    print(f"system insert failed for {rid}: {e}")

        # alerts for anomalies
        if pred == 1:
            # check existing alert for this event
            chk.execute("SELECT 1 FROM alerts WHERE message LIKE %s LIMIT 1", (f"%event {rid}%",))
            if chk.fetchone() is None:
                try:
                    ins_alert.execute("INSERT INTO alerts (timestamp, severity, message) VALUES (CURRENT_TIMESTAMP, %s, %s)", ('HIGH', f"Anomaly detected for event {rid}"))
                except Exception as e:
                    print(f"alert insert failed for {rid}: {e}")

    # commit and close
    conn.commit()
    print("Backfill complete.")
    ins_keystroke.close(); ins_mouse.close(); ins_app.close(); ins_system.close(); ins_alert.close(); chk.close()
    cur.close(); conn.close()

if __name__ == '__main__':
    backfill()
