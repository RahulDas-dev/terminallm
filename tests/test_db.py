import sqlite3
import unittest
from pathlib import Path

from terminallm.app.db.database import Database


# ruff: noqa
class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db = Database()

    def test_init(self):
        self.assertIsInstance(self.db.db_path, Path)
        self.assertEqual(self.db.db_path, Path.home() / ".terminalllm_chat_history.db")

    def test_initilize(self):
        status = self.db.initilize()
        self.assertTrue(status)
        self.assertTrue(self.db.db_path.exists())

    def test_initilize_table_creation(self):
        self.db.initilize()
        connection = sqlite3.connect(self.db.db_path)
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='llmaudit';")
        tables = cursor.fetchall()
        self.assertEqual(len(tables), 1)
        self.assertEqual(tables[0][0], "llmaudit")
        connection.close()

    def test_insert_data(self):
        self.db.initilize()
        chat_history = [{"role": "user", "content": "hello"}, {"role": "assistant", "content": "hi"}]
        llm_config = {"model": "gpt-3.5-turbo"}
        status = self.db.insert_data("qna", chat_history, llm_config)
        self.assertTrue(status)
        connection = sqlite3.connect(self.db.db_path)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM llmaudit;")
        rows = cursor.fetchall()
        self.assertGreater(len(rows), 1)
        connection.close()


if __name__ == "__main__":
    unittest.main()
