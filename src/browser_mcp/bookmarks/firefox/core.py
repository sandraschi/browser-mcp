import logging
import shutil
import sqlite3
import tempfile
from pathlib import Path

from .utils import get_profile_directory

logger = logging.getLogger(__name__)

class FirefoxDatabaseUnlocker:
    @staticmethod
    def copy_database_to_temp(db_path: Path) -> Path | None:
        try:
            with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as temp_file:
                temp_path = Path(temp_file.name)
            shutil.copy2(db_path, temp_path)
            return temp_path
        except (PermissionError, OSError, shutil.Error) as e:
            logger.debug(f"Failed to copy database: {e}")
            if "temp_path" in locals():
                try:
                    temp_path.unlink(missing_ok=True)
                except Exception:
                    pass
            return None

    @staticmethod
    def try_sqlite_tricks(db_path: Path) -> sqlite3.Connection | None:
        connection_attempts = [
            f"file:{db_path}?mode=ro&immutable=1",
            f"file:{db_path}?mode=ro&nolock=1",
            f"file:{db_path}?mode=ro&cache=shared",
            f"file:{db_path}?mode=ro",
            str(db_path),
        ]
        for uri in connection_attempts:
            try:
                if uri.startswith("file:"):
                    conn = sqlite3.connect(uri, uri=True, timeout=1.0)
                else:
                    conn = sqlite3.connect(uri, timeout=1.0)
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                logger.info(f"Successfully opened Firefox DB with: {uri}")
                return conn
            except sqlite3.Error as e:
                logger.debug(f"Failed SQLite method {uri}: {e}")
                continue
        return None

    @staticmethod
    def get_database_connection_bruteforce(db_path: Path) -> tuple[sqlite3.Connection | None, str]:
        if not db_path.exists():
            return None, "Database file does not exist"
        conn = FirefoxDatabaseUnlocker.try_sqlite_tricks(db_path)
        if conn:
            return conn, "sqlite_uri_tricks"
        logger.info("Attempting database copy method...")
        temp_db_path = FirefoxDatabaseUnlocker.copy_database_to_temp(db_path)
        if temp_db_path:
            try:
                conn = sqlite3.connect(f"file:{temp_db_path}?mode=ro", uri=True)
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                logger.info(f"Successfully copied Firefox DB: {temp_db_path}")
                conn.temp_db_path = temp_db_path
                return conn, "database_copy"
            except sqlite3.Error as e:
                logger.debug(f"Failed to use copied database: {e}")
                try:
                    temp_db_path.unlink(missing_ok=True)
                except Exception:
                    pass
        logger.info("Attempting extended timeout method...")
        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5.0)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            logger.info("Successfully opened Firefox DB with extended timeout")
            return conn, "extended_timeout"
        except sqlite3.Error as e:
            logger.debug(f"Extended timeout also failed: {e}")
        return None, "All brute force methods failed - database is locked"

def get_default_profile_path() -> Path | None:
    return get_profile_directory()
