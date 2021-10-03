import sqlite3
from pathlib import Path
from typing import List

from xleapp import globals as g


class TimelineDBManager:

    connection: sqlite3.Connection = None
    report_folder: Path = None
    file: Path = None

    def __init__(self):

        self.report_folder = Path(g.report_folder) / "_Timeline"
        self.report_folder.mkdir(parents=True, exist_ok=True)
        self.file = self.report_folder / "t1.db"

        if not self.file.exists():
            db = sqlite3.connect(self.file, isolation_level="exclusive")
            cursor = db.cursor()
            cursor.execute(
                """
                CREATE TABLE data(key TEXT, activity TEXT, datalist TEXT)
                """,
            )
            db.commit()

    def __enter__(self):
        self.connection = sqlite3.connect(self.file, isolation_level="exclusive")
        self.connection.row_factory = sqlite3.Row
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.commit()
        self.connection.close()


def save(tlactivity: str, data_list: List, data_headers: List[str]) -> None:
    with TimelineDBManager() as db:
        db.connection.execute("""PRAGMA synchronous = EXTRA""")
        db.connection.execute("""PRAGMA journal_mode = WAL""")

        for row in data_list:
            modifiedlist = list(
                map(lambda x, y: x.upper() + ": " + str(y), data_headers, row),
            )
            db.connection.executemany(
                "INSERT INTO data VALUES(?,?,?)",
                [(str(row[0]), tlactivity.upper(), str(modifiedlist))],
            )
