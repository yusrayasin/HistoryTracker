import sqlite3
import tkinter as tk
from tkinter import ttk
import time
from datetime import datetime, timedelta
import logging
import sys
import os
from pathlib import Path
import shutil

# -----------------------------
# LOGGING SETUP
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("=" * 50)
logger.info("APPLICATION STARTING")
logger.info("=" * 50)

# -----------------------------
# CHECK IF tracker.db EXISTS, IF NOT CREATE IT FROM CHROME
# -----------------------------
def ensure_database_exists():
    """Check if tracker.db exists, if not create it from Chrome history"""
    if os.path.exists("tracker.db"):
        logger.info("✅ tracker.db found!")
        return True
    
    logger.warning("tracker.db not found! Creating from Chrome history...")
    
    try:
        # Locate Chrome History
        chrome_history_path = (
            Path.home()
            / "AppData"
            / "Local"
            / "Google"
            / "Chrome"
            / "User Data"
            / "Default"
            / "History"
        )
        
        if not chrome_history_path.exists():
            logger.error(f"Chrome history not found at: {chrome_history_path}")
            logger.error("Please make sure Chrome is installed and you have browsing history.")
            return False
        
        logger.info(f"Found Chrome history at: {chrome_history_path}")
        
        # Copy Chrome History (to avoid locking issues)
        shutil.copy2(chrome_history_path, "History_Copy")
        logger.info("✅ Chrome history copied successfully")
        
        # Read and convert
        conn = sqlite3.connect("History_Copy")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, url, last_visit_time
            FROM urls
            ORDER BY last_visit_time DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            logger.warning("No history found in Chrome! Creating sample data...")
            return create_sample_database()
        
        # Create tracker.db
        tracker = sqlite3.connect("tracker.db")
        t_cursor = tracker.cursor()
        t_cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY,
                title TEXT,
                url TEXT,
                visit_date TEXT,
                visit_time TEXT
            )
        """)
        
        chrome_epoch = datetime(1601, 1, 1)
        count = 0
        
        for id, title, url, timestamp in rows:
            try:
                dt = chrome_epoch + timedelta(microseconds=timestamp) + timedelta(hours=5)
                date_str = dt.strftime("%d-%m-%Y")
                time_str = dt.strftime("%I:%M:%S %p")
                
                t_cursor.execute("INSERT OR IGNORE INTO history VALUES (?, ?, ?, ?, ?)", 
                                 (id, title, url, date_str, time_str))
                count += 1
            except Exception as e:
                logger.debug(f"Skipping record {id}: {e}")
                continue
        
        tracker.commit()
        tracker.close()
        
        logger.info(f"✅ Created tracker.db with {count} records from Chrome history!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create tracker.db: {e}")
        return False

def create_sample_database():
    """Create a sample database with example data"""
    logger.info("Creating sample database with example data...")
    
    try:
        tracker = sqlite3.connect("tracker.db")
        t_cursor = tracker.cursor()
        t_cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY,
                title TEXT,
                url TEXT,
                visit_date TEXT,
                visit_time TEXT
            )
        """)
        
        sample_data = [
            (1, "Google Search", "https://www.google.com", "13-07-2026", "10:30:00 AM"),
            (2, "YouTube - Python Tutorial", "https://www.youtube.com", "13-07-2026", "11:00:00 AM"),
            (3, "GitHub - History Tracker", "https://www.github.com", "13-07-2026", "11:30:00 AM"),
            (4, "Stack Overflow - Python Help", "https://stackoverflow.com", "12-07-2026", "02:15:00 PM"),
            (5, "Wikipedia - Chrome History", "https://www.wikipedia.org", "12-07-2026", "03:45:00 PM"),
        ]
        
        for id, title, url, date, time in sample_data:
            t_cursor.execute("INSERT OR IGNORE INTO history VALUES (?, ?, ?, ?, ?)", 
                           (id, title, url, date, time))
        
        tracker.commit()
        tracker.close()
        
        logger.info("✅ Created sample database with example data!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create sample database: {e}")
        return False

# Run database check before starting
if not ensure_database_exists():
    logger.critical("❌ Could not create database! App cannot continue.")
    input("Press Enter to exit...")
    sys.exit(1)

# -----------------------------
# METRICS TRACKER (Built-in)
# -----------------------------
class MetricsTracker:
    def __init__(self):
        self.metrics = {
            "app_start": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "searches": 0,
            "search_keywords": [],
            "load_more_clicks": 0,
            "records_loaded": 0,
            "load_times": [],
            "errors": 0
        }
        self.start_time = time.time()
        logger.debug("Metrics tracker initialized")
    
    def search_performed(self, keyword):
        self.metrics["searches"] += 1
        if keyword:
            self.metrics["search_keywords"].append(keyword)
            logger.info(f"Search performed: '{keyword}'")
    
    def load_more_clicked(self):
        self.metrics["load_more_clicks"] += 1
        logger.debug("Load More button clicked")
    
    def records_loaded(self, count):
        self.metrics["records_loaded"] += count
        logger.debug(f"Loaded {count} records")
    
    def batch_load_time(self, seconds):
        self.metrics["load_times"].append(seconds)
        logger.debug(f"Batch load time: {seconds:.3f} seconds")
    
    def error_occurred(self, error_msg):
        self.metrics["errors"] += 1
        logger.error(f"Error occurred: {error_msg}")
    
    def app_closed(self):
        uptime = round((time.time() - self.start_time) / 60, 2)
        
        logger.info("=" * 50)
        logger.info("METRICS SUMMARY")
        logger.info("=" * 50)
        logger.info(f"App Started: {self.metrics['app_start']}")
        logger.info(f"Uptime: {uptime} minutes")
        logger.info(f"Total Searches: {self.metrics['searches']}")
        
        # Show top 5 keywords
        if self.metrics['search_keywords']:
            from collections import Counter
            top = Counter(self.metrics['search_keywords']).most_common(5)
            logger.info(f"Top Keywords: {[word for word, count in top]}")
        else:
            logger.info("Top Keywords: []")
        
        logger.info(f"Load More Clicks: {self.metrics['load_more_clicks']}")
        logger.info(f"Records Viewed: {self.metrics['records_loaded']}")
        
        if self.metrics['load_times']:
            avg = sum(self.metrics['load_times']) / len(self.metrics['load_times'])
            logger.info(f"Avg Load Time: {avg:.3f} seconds")
        else:
            logger.info("Avg Load Time: N/A")
        
        logger.info(f"Errors: {self.metrics['errors']}")
        logger.info("=" * 50)

# Create metrics tracker
metrics = MetricsTracker()

# -----------------------------
# Main Window
# -----------------------------
logger.info("Creating main window")

try:
    root = tk.Tk()
    root.title("Chrome History Tracker")
    root.geometry("1200x600")
except Exception as e:
    logger.critical(f"Failed to create main window: {e}")
    sys.exit(1)

# -----------------------------
# Search Label
# -----------------------------
tk.Label(root, text="Search History", font=("Arial", 12, "bold")).pack(pady=5)

# Top Frame for Search and Load More Button
top_frame = tk.Frame(root)
top_frame.pack(pady=5)

search_entry = tk.Entry(top_frame, width=50, font=("Arial", 11))
search_entry.pack(side=tk.LEFT, padx=5)

load_more_btn = tk.Button(top_frame, text="Load More (50)", font=("Arial", 10))
load_more_btn.pack(side=tk.LEFT, padx=5)

# Label to show total records
total_label = tk.Label(root, text="Total: 0 records", font=("Arial", 10, "bold"))
total_label.pack()

# -----------------------------
# Table
# -----------------------------
columns = ("Date", "Time", "Title", "URL")

tree = ttk.Treeview(root, columns=columns, show="headings")

for col in columns:
    tree.heading(col, text=col)

tree.column("Date", width=100)
tree.column("Time", width=100)
tree.column("Title", width=300)
tree.column("URL", width=650)

scrollbar = ttk.Scrollbar(root, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)

tree.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

logger.debug("UI setup complete")

# -----------------------------
# BATCHING VARIABLES
# -----------------------------
BATCH_SIZE = 50  # Load 50 records at a time
current_offset = 0
current_search = ""
total_records = 0
all_records_loaded = False

logger.info(f"Batch size set to {BATCH_SIZE}")

# -----------------------------
# Function to Get Total Records
# -----------------------------
def get_total_records(search_text=""):
    """Get total number of records matching search"""
    try:
        logger.debug(f"Getting total records for: '{search_text}'")
        connection = sqlite3.connect("tracker.db")
        cursor = connection.cursor()

        if search_text == "":
            cursor.execute("SELECT COUNT(*) FROM history")
        else:
            cursor.execute("""
                SELECT COUNT(*) FROM history
                WHERE title LIKE ? OR url LIKE ?
            """, ("%" + search_text + "%", "%" + search_text + "%"))

        total = cursor.fetchone()[0]
        connection.close()
        logger.debug(f"Total records: {total}")
        return total
    except sqlite3.Error as e:
        logger.error(f"Database error in get_total_records: {e}")
        metrics.error_occurred(str(e))
        return 0

# -----------------------------
# Function to Load History (BATCHED)
# -----------------------------
def load_history(search_text="", reset=True):
    """Load history in batches"""
    global current_offset, current_search, all_records_loaded, total_records
    
    logger.info(f"Loading history: search='{search_text}', reset={reset}")
    
    # Start timer for performance metric
    start_time = time.time()

    try:
        if reset:
            # Clear table and reset variables
            for row in tree.get_children():
                tree.delete(row)
            current_offset = 0
            current_search = search_text
            all_records_loaded = False
            total_records = get_total_records(search_text)
            total_label.config(text=f"Total: {total_records} records")
            logger.info(f"Reset complete. Total records: {total_records}")

        connection = sqlite3.connect("tracker.db")
        cursor = connection.cursor()

        # Load only BATCH_SIZE records starting from current_offset
        if search_text == "":
            logger.debug(f"Loading batch: offset={current_offset}, limit={BATCH_SIZE}")
            cursor.execute("""
                SELECT visit_date, visit_time, title, url
                FROM history
                ORDER BY id DESC
                LIMIT ? OFFSET ?
            """, (BATCH_SIZE, current_offset))
        else:
            logger.debug(f"Loading search batch: search='{search_text}', offset={current_offset}")
            cursor.execute("""
                SELECT visit_date, visit_time, title, url
                FROM history
                WHERE title LIKE ? OR url LIKE ?
                ORDER BY id DESC
                LIMIT ? OFFSET ?
            """, ("%" + search_text + "%", "%" + search_text + "%", BATCH_SIZE, current_offset))

        rows = cursor.fetchall()
        connection.close()

        logger.info(f"Loaded {len(rows)} records")
        
        # Track records loaded metric
        if rows:
            metrics.records_loaded(len(rows))

        # Insert rows
        for row in rows:
            tree.insert("", tk.END, values=row)

        # Update offset
        current_offset += len(rows)

        # Check if all records are loaded
        if current_offset >= total_records:
            all_records_loaded = True
            load_more_btn.config(text="All Loaded", state="disabled")
            logger.info("All records loaded")
        else:
            remaining = total_records - current_offset
            load_more_btn.config(
                text=f"Load More ({min(BATCH_SIZE, remaining)} remaining)",
                state="normal"
            )
            logger.debug(f"{remaining} records remaining")

        # Update total label with loaded count
        loaded = len(tree.get_children())
        total_label.config(text=f"Loaded: {loaded} / Total: {total_records} records")
        
        # ============ WARNING LOG: Check if no records found ============
        if len(rows) == 0 and search_text != "":
            logger.warning(f"No results found for search: '{search_text}'")
        
    except sqlite3.Error as e:
        logger.error(f"Database error in load_history: {e}")
        total_label.config(text="ERROR: Failed to load history")
        metrics.error_occurred(str(e))
    except Exception as e:
        logger.error(f"Unexpected error in load_history: {e}")
        total_label.config(text="ERROR: Unexpected error")
        metrics.error_occurred(str(e))
    
    # Track load time
    load_time = time.time() - start_time
    metrics.batch_load_time(load_time)
    logger.debug(f"Batch loaded in {load_time:.3f} seconds")
    
    # ============ WARNING LOG: Check if load time is slow ============
    if load_time > 1.0:
        logger.warning(f"Slow batch load: {load_time:.2f} seconds")
    elif load_time > 0.5:
        logger.debug(f"Moderate load time: {load_time:.3f} seconds")

# -----------------------------
# Load More Function
# -----------------------------
def load_more():
    """Load next batch"""
    logger.info("Load More clicked")
    metrics.load_more_clicked()
    if not all_records_loaded:
        load_history(current_search, reset=False)
    else:
        # ============ WARNING LOG: User clicked but all loaded ============
        logger.warning("Load More clicked but all records already loaded")

# -----------------------------
# Search Event
# -----------------------------
def search(event):
    search_text = search_entry.get()
    if search_text:
        metrics.search_performed(search_text)
        # ============ INFO LOG: Search performed ============
        logger.info(f"Searching for: '{search_text}'")
    load_history(search_text, reset=True)

# -----------------------------
# Bind Events
# -----------------------------
search_entry.bind("<KeyRelease>", search)
load_more_btn.config(command=load_more)

# -----------------------------
# Initial Load
# -----------------------------
logger.info("Performing initial load")

try:
    load_history("", reset=True)
except Exception as e:
    # ============ CRITICAL LOG: App failed to load ============
    logger.critical(f"Failed to load initial history: {e}")
    sys.exit(1)

# -----------------------------
# Close Handler - Save Metrics
# -----------------------------
def on_closing():
    logger.info("Application closing")
    metrics.app_closed()
    logger.info("=" * 50)
    logger.info("APPLICATION CLOSED")
    logger.info("=" * 50)
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

logger.info("Application ready")
root.mainloop()

# ============ CRITICAL LOG: App crashed ============
logger.critical("Application crashed unexpectedly")