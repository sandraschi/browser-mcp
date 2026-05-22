import logging
import sqlite3
from pathlib import Path
from typing import Any


class FirefoxDB:
    def __init__(self, profile_path: Path | None = None):
        self.profile_path = profile_path
        self.conn = None
        self.logger = logging.getLogger(__name__)

    def connect(self) -> bool:
        try:
            if not self.profile_path or not self.profile_path.exists():
                return False
            db_path = self.profile_path / "places.sqlite"
            if not db_path.exists():
                return False
            self.conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            self.conn.row_factory = sqlite3.Row
            return True
        except sqlite3.Error as e:
            self.logger.error(f"Database connection failed: {e}")
            return False

    def execute(self, query: str, params: tuple = ()) -> Any:
        if not self.conn:
            if not self.connect():
                raise ConnectionError("Failed to connect to database")
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            return cursor
        except sqlite3.Error as e:
            self.logger.error(f"Query failed: {e}")
            raise

    def close(self) -> None:
        if self.conn:
            self.conn.close()
            self.conn = None
