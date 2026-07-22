import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import shutil

try:
    import psycopg2
except ImportError:
    print("❌ psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

DB_HOST = os.getenv('DB_HOST', 'postgres')
DB_USER = os.getenv('DB_USER', 'history_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'history_pass')
DB_NAME = os.getenv('DB_NAME', 'history_db')

def main():
    print("=" * 50)
    print("🐘 CHROME HISTORY → POSTGRESQL")
    print("=" * 50)
    
    chrome_path = Path("/root/.config/google-chrome/Default/History")
    print(f"🔍 Looking for Chrome history at: {chrome_path}")
    print(f"📁 File exists: {chrome_path.exists()}")
    
    if not chrome_path.exists():
        print("❌ Chrome history NOT FOUND!")
        return
    
    print(f"📄 File size: {chrome_path.stat().st_size} bytes")
    print("✅ Chrome history FOUND! Reading it now...")
    
    # Connect to PostgreSQL
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        print("✅ Connected to PostgreSQL!")
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return
    
    # Clear existing table (to remove sample data)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS history")
    cursor.execute("""
        CREATE TABLE history (
            id INTEGER PRIMARY KEY,
            title TEXT,
            url TEXT,
            visit_date TEXT,
            visit_time TEXT
        )
    """)
    conn.commit()
    print("✅ Table recreated (sample data removed)")
    
    # Read ALL Chrome history (no LIMIT)
    try:
        copy_path = Path("/tmp/History_Copy")
        shutil.copy2(chrome_path, copy_path)
        
        conn_sqlite = sqlite3.connect(copy_path)
        cursor_sqlite = conn_sqlite.cursor()
        cursor_sqlite.execute("""
            SELECT id, title, url, last_visit_time
            FROM urls
            ORDER BY last_visit_time DESC
        """)
        rows = cursor_sqlite.fetchall()
        conn_sqlite.close()
        copy_path.unlink()
        
        print(f"✅ Found {len(rows)} records from Chrome")
        
        if len(rows) == 0:
            print("⚠️ Chrome history exists but is empty!")
            conn.close()
            return
        
        # Insert into PostgreSQL
        chrome_epoch = datetime(1601, 1, 1)
        count = 0
        
        for id, title, url, timestamp in rows:
            dt = chrome_epoch + timedelta(microseconds=timestamp) + timedelta(hours=5)
            date_str = dt.strftime("%d-%m-%Y")
            time_str = dt.strftime("%I:%M:%S %p")
            
            if not title:
                title = "No Title"
            
            cursor.execute("""
                INSERT INTO history (id, title, url, visit_date, visit_time)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (id, title, url, date_str, time_str))
            count += 1
        
        conn.commit()
        print(f"✅ Inserted {count} records into PostgreSQL")
        
    except Exception as e:
        print(f"❌ Error reading Chrome history: {e}")
    
    # Show summary
    cursor.execute("SELECT COUNT(*) FROM history")
    total = cursor.fetchone()[0]
    print(f"\n📊 Total records in PostgreSQL: {total}")
    
    cursor.execute("SELECT * FROM history LIMIT 5")
    print("\n📋 Sample data:")
    for row in cursor.fetchall():
        print(f"  {row[3]} {row[4]} - {row[1]}")
    
    conn.close()
    print("\n✅ Done!")

if __name__ == "__main__":
    main()