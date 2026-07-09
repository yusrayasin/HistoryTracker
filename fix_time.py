from pathlib import Path
import shutil
import sqlite3
from datetime import datetime, timedelta

print("=" * 60)
print("CHROME HISTORY TO PAKISTAN TIME")
print("=" * 60)

# Copy Chrome History
history_path = Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data" / "Default" / "History"
shutil.copy2(history_path, "History_Copy")
print("✅ History copied")

# Read Chrome History
conn = sqlite3.connect("History_Copy")
cursor = conn.cursor()
cursor.execute("SELECT id, title, url, last_visit_time FROM urls ORDER BY last_visit_time DESC")
rows = cursor.fetchall()
conn.close()

print(f"✅ Found {len(rows)} records")

# Create NEW database
tracker = sqlite3.connect("tracker.db")
t_cursor = tracker.cursor()
t_cursor.execute("CREATE TABLE history (id INTEGER PRIMARY KEY, title TEXT, url TEXT, visit_date TEXT, visit_time TEXT)")

print("✅ Database created")
print("\n" + "=" * 60)
print("CONVERTING TIMESTAMPS:")
print("=" * 60)

count = 0
for id, title, url, timestamp in rows:
    # Convert Chrome timestamp (microseconds since 1601)
    dt = datetime(1601, 1, 1) + timedelta(microseconds=timestamp)
    
    # ADD EXACTLY 5 HOURS for Pakistan
    dt = dt + timedelta(hours=5)
    
    date_str = dt.strftime("%d-%m-%Y")
    time_str = dt.strftime("%I:%M:%S %p")
    
    if count < 5:
        print(f"{count+1}. {date_str} {time_str} - {title[:40]}")
    
    t_cursor.execute("INSERT INTO history VALUES (?, ?, ?, ?, ?)", 
                     (id, title, url, date_str, time_str))
    count += 1

tracker.commit()
tracker.close()

print("=" * 60)
print(f"✅ Saved {count} records with PAKISTAN TIME (UTC+5)!")
print("🎉 DONE!")