import sqlite3
import typing
from pathlib import Path
from re import T
from typing import List

import simplekml
from simplekml import kml

from xleapp import globals as g


class KMLDBManager:

    connection: sqlite3.Connection = None
    report_folder: Path = None
    file: Path = None

    def __enter__(self) -> "KMLDBManager":
        self.connection = sqlite3.connect(self.file, isolation_level="exclusive")
        self.connection.row_factory = sqlite3.Row
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.connection.commit()
        self.connection.close()

    def create(self, report_folder: Path) -> None:

        self.report_folder = Path(report_folder) / "_KML Exports"
        self.report_folder.mkdir(parents=True, exist_ok=True)
        self.file = self.report_folder / '_latlong.db'

        if not self.file.exists():
            db = sqlite3.connect(self.file, isolation_level="exclusive")
            cursor = db.cursor()
            cursor.execute(
                """
                CREATE TABLE data(key TEXT, latitude TEXT, longitude TEXT, activity TEXT)
                """,
            )
            db.commit()


def save(kmlactivity: str, data_list: List, data_headers: List[str]) -> None:
    kml = simplekml.Kml(open=1)

    with _kmldb as db:
        db.connection.execute("""PRAGMA synchronous = EXTRA""")
        db.connection.execute("""PRAGMA journal_mode = WAL""")
        db.connection.commit()

        for row in data_list:
            modifiedDict = dict(zip(data_headers, row))

            times = modifiedDict['Timestamp']
            lon = modifiedDict['Longitude']
            lat = modifiedDict['Latitude']

            if lat:
                pnt = kml.newpoint()
                pnt.name = times
                pnt.description = f'Timestamp: {times} - {kmlactivity}'
                pnt.coords = [(lon, lat)]

                db.connection.execute(
                    "INSERT INTO data VALUES(?,?,?,?)",
                    (times, lat, lon, kmlactivity),
                )

    kml.save(_kmldb.report_folder / f'{kmlactivity}.kml')


def init(report_folder: Path) -> None:
    global _kmldb

    _kmldb = KMLDBManager()
    _kmldb.create(report_folder)


""" Creates the KML DB object used by
    the kmldb.save() function to create the db
    when it is first accesssed (if it does not exists)
    then uses this object to execute each set of values.
"""
_kmldb: KMLDBManager = None
