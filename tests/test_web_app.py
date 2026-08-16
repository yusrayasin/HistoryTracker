import unittest
from unittest.mock import patch

import web_app


class FakeCursor:
    def __init__(self, rows, total_records):
        self.rows = rows
        self.total_records = total_records
        self.executed_sql = None
        self.executed_params = None
        self._result = None

    def execute(self, query, params=None):
        self.executed_sql = query
        self.executed_params = params
        if "SELECT COUNT(*)" in query.upper():
            self._result = [(self.total_records,)]
        else:
            self._result = self.rows

    def fetchone(self):
        return self._result[0] if self._result else (0,)

    def fetchall(self):
        return self._result if self._result else self.rows


class FakeConnection:
    def __init__(self, rows, total_records=2):
        self.cursor_obj = FakeCursor(rows, total_records)

    def cursor(self):
        return self.cursor_obj

    def close(self):
        return None


class WebAppPaginationTests(unittest.TestCase):
    def test_index_shows_paged_count_and_load_more(self):
        fake_rows = [("2024-01-01", "12:00", "Example", "https://example.com")]

        with patch.object(web_app, "get_db_connection", return_value=FakeConnection(fake_rows, total_records=2)):
            client = web_app.app.test_client()
            response = client.get("/")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Showing 1 of 2 records", html)
        self.assertIn("Load More", html)


if __name__ == "__main__":
    unittest.main()
