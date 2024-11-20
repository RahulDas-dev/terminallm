import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict

# Connect to the SQLite database (or create it)

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.db_path = Path.home() / ".terminalllm_chat_history.db"

    def initilize(self) -> bool:
        status = True
        # Create a cursor object
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        # Create a table with the specified columns
        try:
            cursor.execute("""CREATE TABLE IF NOT EXISTS llmaudit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_mode TEXT,
                llm_config JSON,
                chat_history JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );""")
        except Exception as err:
            status = False
            logger.exception(err)
        else:
            connection.commit()
        # Close the connection
        finally:
            connection.close()
        return status

    def insert_data(self, app_mode: str, chat_history: Dict[str, str], llm_config: Dict[str, str]) -> bool:
        # Create a cursor object
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        status = True
        created_at = datetime.now().isoformat()  # Current datetime in ISO format
        chat_history = json.dumps(chat_history)  # Chat history as JSON
        llm_config = json.dumps(llm_config)  # LLM configuration as JSON
        try:
            # Insert data into the users table
            cursor.execute(
                """
            INSERT INTO llmaudit (app_mode, llm_config, chat_history, created_at) VALUES (?, ?, ?, ?)
            """,
                (app_mode, llm_config, chat_history, created_at),
            )
        except Exception as err:
            status = False
            connection.rollback()
            logger.exception(err)
        else:
            connection.commit()
        finally:
            connection.close()
        return status
