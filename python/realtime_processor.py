import time
import json
import os
from collections import deque

import jpype
import jaydebeapi

# Configuration - adjust if needed
JAR = r"D:\Downloads\mysql-connector-j-9.4.0\mysql-connector-j-9.4.0\mysql-connector-j-9.4.0.jar"
DRV = 'com.mysql.cj.jdbc.Driver'
URL = 'jdbc:mysql://localhost:3306/neurolock'
USER = 'root'
PASS = 'JoeMama@25'

# Anomaly thresholds
KEYSTROKE_WINDOW_S = 10
KEYSTROKE_THRESHOLD = 30  # if >30 keystrokes in 10s -> alert


def find_jvm():
    candidates = [os.environ.get('JAVA_HOME'), r"C:\Program Files\Java"]
    for c in candidates:
        if not c:
            continue
        if os.path.exists(c):
            for p in __import__('pathlib').Path(c).rglob('jvm.dll'):
                return str(p)
    return None


def ensure_jvm(jar):
    if not jpype.isJVMStarted():
        jvm = find_jvm()
        if jvm:
            jpype.startJVM(jvm, '-Djava.class.path=' + jar)
        else:
            jpype.startJVM(jpype.getDefaultJVMPath(), '-Djava.class.path=' + jar)


class RealtimeProcessor:
    def __init__(self):
        ensure_jvm(JAR)
        self.conn = jaydebeapi.connect(DRV, URL, [USER, PASS], JAR)
        self.keystroke_times = deque()

    def close(self):
        try:
            if self.conn:
                self.conn.close()
        except:
            pass

    def run_once(self):
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT id, timestamp, event_type, raw_data FROM behavior_logs WHERE processed_at IS NULL ORDER BY id ASC LIMIT 200")
            rows = cur.fetchall()
            if not rows:
                return 0

            for r in rows:
                _id, ts, etype, raw = r
                try:
                    payload = json.loads(raw) if raw else {}
                except Exception:
                    payload = {'raw': raw}

                # Route events
                try:
                    if 'KEY' in (etype or ''):
                        self.insert_keystroke(ts, etype, payload)
                        self.check_keystroke_anomaly(ts)
                    elif 'MOUSE' in (etype or ''):
                        self.insert_mouse(ts, etype, payload)
                    elif 'APP' in (etype or '') or 'APPLICATION' in (etype or ''):
                        self.insert_app(ts, etype, payload)
                    elif 'SYSTEM' in (etype or ''):
                        self.insert_system(ts, etype, payload)
                    else:
                        self.insert_behavior(ts, etype, payload)
                except Exception as e:
                    print(f"Error routing event id={_id}: {e}")

                # mark processed
                try:
                    ucur = self.conn.cursor()
                    ucur.execute("UPDATE behavior_logs SET processed_at = NOW() WHERE id = ?", (_id,))
                    self.conn.commit()
                    ucur.close()
                except Exception as e:
                    print(f"Failed to mark processed id={_id}: {e}")

            return len(rows)
        finally:
            cur.close()

    def insert_keystroke(self, ts, etype, payload):
        # Attempt to insert into keystroke_events; fallback to behavior_events
        try:
            c = self.conn.cursor()
            c.execute("INSERT INTO keystroke_events (timestamp, event_type, raw_data) VALUES (?, ?, ?)", (ts, etype, json.dumps(payload)))
            self.conn.commit()
            c.close()
        except Exception:
            try:
                c = self.conn.cursor()
                c.execute("INSERT INTO behavior_events (timestamp, event_type, raw_data) VALUES (?, ?, ?)", (ts, etype, json.dumps(payload)))
                self.conn.commit()
                c.close()
            except Exception as e:
                print(f"Failed keystroke insert fallback: {e}")

    def insert_mouse(self, ts, etype, payload):
        try:
            c = self.conn.cursor()
            c.execute("INSERT INTO mouse_events (timestamp, event_type, raw_data) VALUES (?, ?, ?)", (ts, etype, json.dumps(payload)))
            self.conn.commit()
            c.close()
        except Exception:
            try:
                c = self.conn.cursor()
                c.execute("INSERT INTO behavior_events (timestamp, event_type, raw_data) VALUES (?, ?, ?)", (ts, etype, json.dumps(payload)))
                self.conn.commit()
                c.close()
            except Exception as e:
                print(f"Failed mouse insert fallback: {e}")

    def insert_app(self, ts, etype, payload):
        try:
            c = self.conn.cursor()
            c.execute("INSERT INTO application_events (timestamp, event_type, raw_data) VALUES (?, ?, ?)", (ts, etype, json.dumps(payload)))
            self.conn.commit()
            c.close()
        except Exception:
            try:
                c = self.conn.cursor()
                c.execute("INSERT INTO behavior_events (timestamp, event_type, raw_data) VALUES (?, ?, ?)", (ts, etype, json.dumps(payload)))
                self.conn.commit()
                c.close()
            except Exception as e:
                print(f"Failed app insert fallback: {e}")

    def insert_system(self, ts, etype, payload):
        try:
            c = self.conn.cursor()
            c.execute("INSERT INTO system_metrics (timestamp, event_type, raw_data) VALUES (?, ?, ?)", (ts, etype, json.dumps(payload)))
            self.conn.commit()
            c.close()
        except Exception:
            try:
                c = self.conn.cursor()
                c.execute("INSERT INTO behavior_events (timestamp, event_type, raw_data) VALUES (?, ?, ?)", (ts, etype, json.dumps(payload)))
                self.conn.commit()
                c.close()
            except Exception as e:
                print(f"Failed system insert fallback: {e}")

    def insert_behavior(self, ts, etype, payload):
        try:
            c = self.conn.cursor()
            c.execute("INSERT INTO behavior_events (timestamp, event_type, raw_data) VALUES (?, ?, ?)", (ts, etype, json.dumps(payload)))
            self.conn.commit()
            c.close()
        except Exception as e:
            print(f"Failed behavior insert: {e}")

    def check_keystroke_anomaly(self, ts):
        # ts expected as epoch or timestamp string; normalize to epoch seconds
        tsec = None
        try:
            tsec = float(ts)
        except Exception:
            try:
                # try parsing as SQL timestamp
                from datetime import datetime
                t = datetime.fromisoformat(str(ts))
                tsec = t.timestamp()
            except Exception:
                tsec = time.time()

        now = tsec
        self.keystroke_times.append(now)
        # trim
        while self.keystroke_times and (now - self.keystroke_times[0]) > KEYSTROKE_WINDOW_S:
            self.keystroke_times.popleft()

        if len(self.keystroke_times) >= KEYSTROKE_THRESHOLD:
            # create alert
            try:
                c = self.conn.cursor()
                msg = f"High keystroke rate: {len(self.keystroke_times)} in {KEYSTROKE_WINDOW_S}s"
                c.execute("INSERT INTO alerts (timestamp, message, severity) VALUES (NOW(), ?, ?)", (msg, 'high'))
                # update anomaly_stats simple counter
                try:
                    c.execute("INSERT INTO anomaly_stats (metric, count, last_updated) VALUES ('keystroke_rate', 1, NOW()) ON DUPLICATE KEY UPDATE count = count + 1, last_updated = NOW()")
                except Exception:
                    # if table lacks ON DUPLICATE, try update/insert
                    pass
                self.conn.commit()
                c.close()
                print(f"ALERT: {msg}")
                # clear to avoid repeat alerts spamming
                self.keystroke_times.clear()
            except Exception as e:
                print(f"Failed to insert alert: {e}")


def main():
    print("Realtime processor starting")
    rp = RealtimeProcessor()
    try:
        while True:
            try:
                cnt = rp.run_once()
                if cnt:
                    print(f"Processed {cnt} rows")
                time.sleep(1)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print("Processor error:", e)
                time.sleep(2)
    finally:
        rp.close()


if __name__ == '__main__':
    main()
