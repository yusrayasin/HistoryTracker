from pathlib import Path
import shutil
import sqlite3
from datetime import datetime, timedelta

print("Fixing...")

history_path = Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data" / "Default" / "History"
shutil.copy2(history_path, "History_Copy")

conn = sqlite3.connect("History_Copy")
cursor = conn.cursor()
cursor.execute("SELECT id, title, url, last_visit_time FROM urls")
rows = cursor.fetchall()
conn.close()

tracker = sqlite3.connect("tracker.db")
t_cursor = tracker.cursor()
t_cursor.execute("CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, title TEXT, url TEXT, visit_date TEXT, visit_time TEXT)")

count = 0
for id, title, url, ts in rows:
    dt = datetime(1601,1,1) + timedelta(microseconds=ts) + timedelta(hours=5)
    date_str = dt.strftime("%d-%m-%Y")
    time_str = dt.strftime("%I:%M:%S %p")
    t_cursor.execute("INSERT OR IGNORE INTO history VALUES (?, ?, ?, ?, ?)", (id, title, url, date_str, time_str))
    count += 1

tracker.commit()
tracker.close()

print(f"DONE! Saved {count} records!")