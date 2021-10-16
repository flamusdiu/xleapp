import os
import sqlite3

from .utils import is_platform_windows


def open_sqlite_db_readonly(path: str) -> sqlite3.Connection:
    """Opens an sqlite db in read-only mode, so original db
    (and -wal/journal are intact)
    """
    if is_platform_windows():
        if path.startswith("\\\\?\\UNC\\"):  # UNC long path
            path = "%5C%5C%3F%5C" + path[4:]
        elif path.startswith("\\\\?\\"):  # normal long path
            path = "%5C%5C%3F%5C" + path[4:]
        elif path.startswith("\\\\"):  # UNC path
            path = "%5C%5C%3F%5C\\UNC" + path[1:]
        else:  # normal path
            path = "%5C%5C%3F%5C" + path
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


def does_column_exist_in_db(
    db: sqlite3.Connection, table_name: str, col_name: str
) -> bool:
    """Checks if a specific col exists"""
    col_name = col_name.lower()
    try:
        db.row_factory = sqlite3.Row  # For fetching columns by name
        query = f"pragma table_info('{table_name}');"
        cursor = db.cursor()
        cursor.execute(query)
        all_rows = cursor.fetchall()
        for row in all_rows:
            if row["name"].lower() == col_name:
                return True
    except sqlite3.Error as ex:
        # logfunc(f"Query error, query={query} Error={str(ex)}")
        pass
    return False


def does_table_exist(db: sqlite3.Connection, table_name: str) -> bool:
    """Checks if a table with specified name exists in an sqlite db"""
    try:
        query = (
            f"SELECT name FROM sqlite_master "
            f"WHERE type='table' AND name='{table_name}'"
        )
        cursor = db.execute(query)
        for row in cursor:
            return True
    except sqlite3.Error as ex:
        # logfunc(f"Query error, query={query} Error={str(ex)}")
        pass
    return False
