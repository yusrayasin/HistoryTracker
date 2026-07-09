import sqlite3

connection = sqlite3.connect("tracker.db")
cursor = connection.cursor()

cursor.execute("""
SELECT *
FROM history
LIMIT 20;
""")

rows = cursor.fetchall()

for row in rows:
    print(row)

connection.close()