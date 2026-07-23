import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import shutil
import time

try:
    import psycopg2
except ImportError:
    print("❌ psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

DB_HOST = os.getenv('DB_HOST', 'postgres')
DB_USER = os.getenv('DB_USER', 'history_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'history_pass')
DB_NAME = os.getenv('DB_NAME', 'history_db')

def wait_for_postgres(max_attempts=15, delay=2):
    """Wait for PostgreSQL to be ready"""
    print("⏳ Waiting for PostgreSQL to be ready...")
    for attempt in range(max_attempts):
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                connect_timeout=2
            )
            conn.close()
            print("✅ PostgreSQL is ready!")
            return True
        except Exception as e:
            print(f"⏳ Waiting... (attempt {attempt + 1}/{max_attempts})")
            time.sleep(delay)
    print("❌ PostgreSQL not available after waiting.")
    return False

def find_chrome_history():
    """Auto-detect Chrome history path"""
    possible_paths = [
        # Docker container path
        Path("/root/.config/google-chrome/Default/History"),
        # Windows paths
        Path(os.path.expanduser("~")) / "AppData/Local/Google/Chrome/User Data/Default/History",
        Path("C:/Users") / os.getenv("USERNAME", "") / "AppData/Local/Google/Chrome/User Data/Default/History",
        # Linux paths
        Path.home() / ".config/google-chrome/Default/History",
        Path.home() / ".cache/google-chrome/Default/History",
    ]
    
    # Check if CHROME_PATH environment variable is set
    env_path = os.getenv("CHROME_PATH")
    if env_path:
        path = Path(env_path)
        if path.exists():
            return path
    
    for path in possible_paths:
        if path.exists():
            return path
    return None

def main():
    print("=" * 50)
    print("🐘 CHROME HISTORY → POSTGRESQL")
    print("=" * 50)
    
    # Wait for PostgreSQL
    if not wait_for_postgres():
        sys.exit(1)
    
    # Auto-detect Chrome history
    chrome_path = find_chrome_history()
    print(f"🔍 Looking for Chrome history...")
    
    if not chrome_path:
        print("❌ Chrome history NOT FOUND!")
        print("💡 Make sure Chrome is installed and you have browsing history.")
        return
    
    print(f"📂 Found Chrome history at: {chrome_path}")
    print(f"📄 File size: {chrome_path.stat().st_size} bytes")
    
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
    
    # Recreate table (clear old data)
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
    print("✅ Table recreated")
    
    # Read ALL Chrome history
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