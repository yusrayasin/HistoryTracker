from pathlib import Path
import shutil
import sqlite3
import time
from datetime import datetime, timedelta

# ------------------------------------
# Chrome History Location
# ------------------------------------
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

copy_path = Path("History_Copy")

print("🚀 Chrome History Monitor Started...\n")

while True:

    # -----------------------------
    # Get highest saved ID
    # -----------------------------
    tracker_connection = sqlite3.connect("tracker.db")
    tracker_cursor = tracker_connection.cursor()

    tracker_cursor.execute("""
    SELECT MAX(id)
    FROM history;
    """)

    result = tracker_cursor.fetchone()

    if result[0] is None:
        last_id = 0
    else:
        last_id = result[0]

    tracker_connection.close()

    # -----------------------------
    # Copy Chrome History
    # -----------------------------
    shutil.copy2(history_path, copy_path)

    connection = sqlite3.connect(copy_path)
    cursor = connection.cursor()

    # -----------------------------
    # Read ONLY new history
    # -----------------------------
    cursor.execute("""
    SELECT
        id,
        title,
        url,
        last_visit_time
    FROM urls
    WHERE id > ?
    ORDER BY id;
    """, (last_id,))

    rows = cursor.fetchall()

    connection.close()

    if len(rows) == 0:
        time.sleep(5)
        continue

    tracker_connection = sqlite3.connect("tracker.db")
    tracker_cursor = tracker_connection.cursor()

    chrome_epoch = datetime(1601, 1, 1)

    for id, title, url, last_visit_time in rows:

        visit_datetime = chrome_epoch + timedelta(
            microseconds=last_visit_time
        )

        visit_date = visit_datetime.strftime("%d-%m-%Y")
        visit_time = visit_datetime.strftime("%I:%M:%S %p")

        tracker_cursor.execute("""
        INSERT OR IGNORE INTO history
        (id, title, url, visit_date, visit_time)
        VALUES (?, ?, ?, ?, ?)
        """, (
            id,
            title,
            url,
            visit_date,
            visit_time
        ))

        print(f"New History -> {title}")

    tracker_connection.commit()
    tracker_connection.close()

    time.sleep(5)