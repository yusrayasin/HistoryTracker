import sqlite3
import tkinter as tk
from tkinter import ttk

# -----------------------------
# Main Window
# -----------------------------
root = tk.Tk()
root.title("Chrome History Tracker")
root.geometry("1200x600")

# -----------------------------
# Search Label
# -----------------------------
tk.Label(root, text="Search History", font=("Arial", 12, "bold")).pack(pady=5)

search_entry = tk.Entry(root, width=60, font=("Arial", 11))
search_entry.pack(pady=5)

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


# -----------------------------
# Function to Load History
# -----------------------------
def load_history(search_text=""):

    connection = sqlite3.connect("tracker.db")
    cursor = connection.cursor()

    for row in tree.get_children():
        tree.delete(row)

    if search_text == "":
        cursor.execute("""
        SELECT visit_date, visit_time, title, url
        FROM history
        ORDER BY id DESC
        """)
    else:
        cursor.execute("""
        SELECT visit_date, visit_time, title, url
        FROM history
        WHERE
            title LIKE ?
            OR url LIKE ?
        ORDER BY id DESC
        """, (
            "%" + search_text + "%",
            "%" + search_text + "%"
        ))

    rows = cursor.fetchall()

    for row in rows:
        tree.insert("", tk.END, values=row)

    connection.close()


# -----------------------------
# Search Event
# -----------------------------
def search(event):
    load_history(search_entry.get())


search_entry.bind("<KeyRelease>", search)

# Initial Load
load_history()

root.mainloop()