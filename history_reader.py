from pathlib import Path
import shutil
import sqlite3
from datetime import datetime, timedelta

# -----------------------------
# Locate Chrome History
# -----------------------------
history_path = (
    Path.home()
    / "AppData"
    / "Local"
    / "Google"
    / "Chrome"
    / "User Data"
    / "Default"
    / "History"
)

# Copy Chrome History database
copy_path = Path("History_Copy")
shutil.copy2(history_path, copy_path)

# -----------------------------
# Read Chrome History
# -----------------------------
connection = sqlite3.connect(copy_path)
cursor = connection.cursor()

cursor.execute("""
SELECT
    id,
    title,
    url,
    last_visit_time
FROM urls
ORDER BY last_visit_time DESC;
""")

rows = cursor.fetchall()
connection.close()

print(f"Found {len(rows)} history records.\n")

# -----------------------------
# Create Our Own Database
# -----------------------------
tracker_connection = sqlite3.connect("tracker.db")
tracker_cursor = tracker_connection.cursor()

# DROP the old table to start fresh
tracker_cursor.execute("DROP TABLE IF EXISTS history")

tracker_cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY,
    title TEXT,
    url TEXT,
    visit_date TEXT,
    visit_time TEXT
)
""")

print("✅ history table created!")

# -----------------------------
# Save Chrome History with PAKISTAN TIME
# -----------------------------
chrome_epoch = datetime(1601, 1, 1)
count = 0

print("\n🔍 Converting to Pakistan Time (UTC+5)...")
print("-" * 60)

for id, title, url, last_visit_time in rows:

    # STEP 1: Convert Chrome timestamp
    visit_datetime_utc = chrome_epoch + timedelta(microseconds=last_visit_time)
    
    # STEP 2: ADD 5 HOURS for Pakistan time
    visit_datetime_pakistan = visit_datetime_utc + timedelta(hours=5)

    visit_date = visit_datetime_pakistan.strftime("%d-%m-%Y")
    visit_time = visit_datetime_pakistan.strftime("%I:%M:%S %p")

    # Show first 5 records for verification
    if count < 5:
        print(f"Record {count+1}: {visit_date} at {visit_time}")
        print(f"  Title: {title[:50]}...")
        print("-" * 60)

    tracker_cursor.execute("""
    INSERT OR IGNORE INTO history
    (id, title, url, visit_date, visit_time)
    VALUES (?, ?, ?, ?, ?)
    """, (id, title, url, visit_date, visit_time))
    
    count += 1

tracker_connection.commit()
tracker_connection.close()

print(f"\n✅ {count} history records saved into tracker.db with Pakistan Time!")
print("🎉 Done!")