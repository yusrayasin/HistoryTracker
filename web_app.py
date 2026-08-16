from flask import Flask, render_template, request
import psycopg2
import os

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST', 'postgres')
DB_USER = os.getenv('DB_USER', 'history_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'history_pass')
DB_NAME = os.getenv('DB_NAME', 'history_db')
PAGE_SIZE = 100


def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )


@app.route('/')
def index():
    search = request.args.get('search', '').strip()
    offset_value = request.args.get('offset', '0')

    try:
        offset = max(0, int(offset_value))
    except (TypeError, ValueError):
        offset = 0

    conn = get_db_connection()
    cursor = conn.cursor()

    if search:
        cursor.execute("""
            SELECT COUNT(*)
            FROM history
            WHERE title ILIKE %s OR url ILIKE %s
        """, (f'%{search}%', f'%{search}%'))
        total_records = cursor.fetchone()[0]

        cursor.execute("""
            SELECT visit_date, visit_time, title, url
            FROM history
            WHERE title ILIKE %s OR url ILIKE %s
            ORDER BY id DESC
            LIMIT %s OFFSET %s
        """, (f'%{search}%', f'%{search}%', PAGE_SIZE, offset))
    else:
        cursor.execute("SELECT COUNT(*) FROM history")
        total_records = cursor.fetchone()[0]

        cursor.execute("""
            SELECT visit_date, visit_time, title, url
            FROM history
            ORDER BY id DESC
            LIMIT %s OFFSET %s
        """, (PAGE_SIZE, offset))

    rows = cursor.fetchall()
    conn.close()

    shown_count = min(offset + len(rows), total_records)
    has_more = (offset + len(rows)) < total_records
    next_offset = offset + PAGE_SIZE

    return render_template(
        'index.html',
        rows=rows,
        search=search,
        total_records=total_records,
        shown_count=shown_count,
        has_more=has_more,
        next_offset=next_offset,
        page_size=PAGE_SIZE
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)