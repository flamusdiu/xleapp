import sqlite3
from pathlib import Path
from typing import List


class TimelineDBManager:
    def __init__(self, tl_report_folder: str, isolation_level=None):
        path = None
        if isinstance(tl_report_folder, str):
            path = Path(tl_report_folder)
        else:
            path = tl_report_folder

        self.file = path / "t1.db"
        if not self.file.exists():
            self._create()

        self.connection = None

    def __enter__(self):
        db = sqlite3.connect(self.file)
        self.connection = db.cursor()
        return self

    def __exit__(self):
        self.connection.close()

    def _create(self):

        db = sqlite3.connect(self.file, isolation_level='exclusive')
        cursor = db.cursor()
        cursor.execute(
            """
            CREATE TABLE data(key TEXT, activity TEXT, datalist TEXT)
            """
        )
        db.commit()


def save(tlactivity: str, data_list: List, data_headers: List[str]) -> None:
    with _timelineDB as db:
        db.execute('''PRAGMA synchronous = EXTRA''')
        db.execute('''PRAGMA journal_mode = WAL''')

        for row in data_list:
            modifiedList = list(map(lambda x, y: x.upper() + ': ' + str(y),
                                data_headers, row))
            db.executemany("INSERT INTO data VALUES(?,?,?)",
                           [(str(row[0]), tlactivity.upper(),
                             str(modifiedList))])


''' Creates the Timeline DB object used by
    the timeline.save() function to create the db
    when it is first accesssed (if it does not exists)
    then uses this object to execute each set of values.
'''
_timelineDB = TimelineDBManager()
