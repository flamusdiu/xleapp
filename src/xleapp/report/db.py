# -*- coding: utf-8 -*-
"""[summary]
"""

import codecs
import csv
import sqlite3
import typing as t

from abc import abstractmethod
from pathlib import Path

import simplekml

from xleapp.helpers.descriptors import Validator


class Options:
    def __set_name__(self, owner, name) -> None:
        self.name = str(name)

    def __get__(self, obj, obj_type=None) -> dict:
        return obj.__dict__.get(self.name) or {}

    def __set__(self, obj, options) -> None:
        if not isinstance(options, dict):
            raise TypeError(f"{self.name!r} is {type(options)!r} instead of {dict!r}!")
        obj.__dict__[self.name] = options["options"]
        for name, option in options["options"].items():
            if name in ["file", "data_list", "data_headers"]:
                obj.__dict__[name] = option


class DBFile(Validator):
    def validator(self, value):
        if isinstance(value, (Path, str)):
            file_path = Path(value)
            if file_path.exists():
                self._create()
            else:
                raise FileExistsError(
                    f"Folder {value!r} does not exists! Failed to create database file!"
                )
        else:
            raise TypeError(f"Expected {value!r} to be Path or str!")


class DBManager:
    connection: t.Union[sqlite3.Connection, codecs.StreamReaderWriter]
    report_folder: Path
    db_file: DBFile = DBFile()
    options: Options = Options()
    data_list: list
    data_headers: t.Union[list[tuple], tuple]
    name: str

    def __init__(
        self,
        report_folder: Path,
        db_folder: t.Union[Path, str],
        options: dict,
    ) -> None:
        self.report_folder = report_folder / db_folder
        self.report_folder.mkdir(parents=True, exist_ok=True)
        self.options = options

    def __enter__(self) -> "DBManager":
        self.connection = sqlite3.connect(self.db_file, isolation_level="exclusive")
        self.connection.row_factory = sqlite3.Row
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.connection.commit()

    @abstractmethod
    def save(self) -> None:
        """Saves files to database

        Returns:
            None
        """
        NotImplementedError(f"{self!r} requires a `save()` function!")

    @abstractmethod
    def _create(self) -> None:
        """Creates database file

        Returns:
            None
        """
        NotImplementedError(f"{self!r} requires a `_create()` function!")


class KmlDBManager(DBManager):
    def __init__(self, report_folder: Path, **options) -> None:
        super().__init__(
            report_folder=report_folder,
            db_folder="_KML_Exports",
            options=options,
        )
        self.db_file = self.report_folder / "_latlong.db"

    def _create(self):
        if not self.db_file.exists():
            db = sqlite3.connect(self.db_file, isolation_level="exclusive")
            cursor = db.cursor()
            cursor.execute(
                """
                CREATE TABLE data(key TEXT, latitude TEXT, longitude TEXT, activity TEXT)
                """,
            )
            db.commit()

    def save(self) -> None:
        kml = simplekml.Kml(open=1)

        with KmlDBManager(self.report_folder) as db:
            db.connection.execute("""PRAGMA synchronous = EXTRA""")
            db.connection.execute("""PRAGMA journal_mode = WAL""")
            db.connection.commit()

            for row in self.data_list:
                modifiedDict = dict(zip(self.data_headers, row))

                times = modifiedDict["Timestamp"]
                lon = modifiedDict["Longitude"]
                lat = modifiedDict["Latitude"]

                if lat:
                    pnt = kml.newpoint()
                    pnt.name = times
                    pnt.description = f"Timestamp: {times} - {self.name}"
                    pnt.coords = [(lon, lat)]

                    db.connection.execute(
                        "INSERT INTO data VALUES(?,?,?,?)",
                        (times, lat, lon, self.name),
                    )

            kml.save(db.report_folder / f"{self.name}.kml")


class TimelineDBManager(DBManager):
    def __init__(self, report_folder: Path, **options):
        super().__init__(
            report_folder=report_folder,
            db_folder="_Timeline",
            options=options,
        )
        self.db_file = self.report_folder / "t1.db"

    def _create(self):
        if not self.db_file.exists():
            db = sqlite3.connect(self.db_file, isolation_level="exclusive")
            cursor = db.cursor()
            cursor.execute(
                """
                CREATE TABLE data(key TEXT, activity TEXT, datalist TEXT)
                """,
            )
            db.commit()

    def save(self) -> None:
        with TimelineDBManager(self.report_folder) as db:
            db.connection.execute("""PRAGMA synchronous = EXTRA""")
            db.connection.execute("""PRAGMA journal_mode = WAL""")

            for row in self.data_list:
                modifiedlist = list(
                    map(lambda x, y: x.upper() + ": " + str(y), self.data_headers, row),
                )
                db.connection.executemany(
                    "INSERT INTO data VALUES(?,?,?)",
                    [(str(row[0]), self.name.upper(), str(modifiedlist))],
                )


class TsvManager(DBManager):
    def __init__(self, report_folder: Path, **options):
        super().__init__(
            report_folder=report_folder,
            db_folder="_TSV Exports",
            options=options,
        )
        self.db_file = f"{self.db_file}.tsv"

    def _create(self):
        pass

    def __enter__(self):
        self.connection = codecs.open(self.db_file, "a", "utf-8-sig")
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.connection.close()

    def save(self):

        with self as file:
            tsv_writer = csv.writer(file, delimiter="\t")
            tsv_writer.writerow(self.data_headers)
            for i in self.data_list:
                tsv_writer.writerow(i)
