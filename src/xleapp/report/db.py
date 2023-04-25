"""[summary]
"""
from __future__ import annotations

import abc
import codecs
import contextlib
import csv
import pathlib
import sqlite3
import typing as t

from dataclasses import dataclass

import simplekml

from xleapp.helpers import descriptors, utils


class DatabaseError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message


class Options:
    def __set_name__(self, owner, name) -> None:
        self.name = str(name)

    def __get__(self, obj, obj_type=None) -> dict:
        return obj.__dict__.get(self.name) or {}

    def __set__(self, obj, options) -> None:
        if not isinstance(options, dict):
            raise TypeError(
                f"{repr(self.name)} is {repr(type(options))} instead of {repr(dict)}!"
            )
        obj.__dict__[self.name] = options
        for name, option in options.items():
            if name in ["name", "data_list", "data_headers"]:
                obj.__dict__[name] = option


class DBFile(descriptors.Validator):
    default_value = pathlib.Path()

    def validator(self, value) -> pathlib.Path | None:
        if not isinstance(value, (pathlib.Path, str)):
            raise TypeError(f"Expected {repr(value)} to be pathlib.Path or str!")
        elif utils.is_platform_windows():
            return pathlib.Path(f"\\\\?\\{value.resolve()}")


class DBManager(contextlib.AbstractContextManager):
    connection: t.Union[sqlite3.Connection, codecs.StreamReaderWriter]
    db_file: DBFile = DBFile()
    db_folder: pathlib.Path = None

    def __init__(self, db_folder: pathlib.Path) -> None:
        if not self.db_folder:
            self.db_folder = db_folder
            self.db_folder.mkdir(parents=True, exist_ok=True)

    def __enter__(self) -> t.Type[DBManager]:
        self.connection = sqlite3.connect(self.db_file, isolation_level="exclusive")
        self.connection.row_factory = sqlite3.Row
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.connection.commit()

    def __str__(self) -> str:
        return (
            f"{type(self).__name__} using folder located at {self.db_folder} to "
            "save database files."
        )

    def __repr__(self) -> str:
        return f"<{type(self).__name__} db_folder={repr(self.db_folder)}>"

    @abc.abstractmethod
    def save(self, name: str, data_list, data_headers) -> None:
        """Saves files to database

        Returns:
            None
        """
        raise NotImplementedError(f"{repr(self)} requires a `save()` function!")

    @abc.abstractmethod
    def create(self) -> None:
        """Creates database file

        Returns:
            None
        """
        raise NotImplementedError(f"{repr(self)} requires a `create()` function!")


class KmlDBManager(DBManager):
    def __init__(self, report_folder: pathlib.Path) -> None:
        db_folder = "_KML_Exports"
        super().__init__(db_folder=report_folder / db_folder)
        self.db_file = report_folder / db_folder / "_latlong.db"

    def create(self) -> None:
        if not self.db_file.exists():
            db = sqlite3.connect(self.db_file, isolation_level="exclusive")
            cursor = db.cursor()
            cursor.execute(
                """
                CREATE TABLE data(key TEXT, latitude TEXT, longitude TEXT, activity TEXT)
                """,
            )
            db.commit()

    def save(self, data_headers, data_list, name) -> None:
        kml = simplekml.Kml(open=1)

        with self as db:
            db.connection.execute("""PRAGMA synchronous = EXTRA""")
            db.connection.execute("""PRAGMA journal_mode = WAL""")
            db.connection.commit()

            for row in data_list:
                modified_dict = dict(zip(data_headers, row))
                times = modified_dict["Timestamp"]
                lon = modified_dict["Longitude"]
                lat = modified_dict["Latitude"]

                if lat:
                    pnt = kml.newpoint()
                    pnt.name = times
                    pnt.description = f"Timestamp: {times} - {name}"
                    pnt.coords = [(lon, lat)]

                    db.connection.execute(
                        "INSERT INTO data VALUES(?,?,?,?)",
                        (times, lat, lon, name),
                    )

            kml.save(db.db_folder / f"{name}.kml")


class TimelineDBManager(DBManager):
    def __init__(self, report_folder: pathlib.Path) -> None:
        db_folder = "_Timeline"

        super().__init__(db_folder=report_folder / db_folder)
        self.db_file = report_folder / db_folder / "t1.db"
        self.create()

    def create(self) -> None:
        if not self.db_file.exists():
            db = sqlite3.connect(self.db_file, isolation_level="exclusive")
            cursor = db.cursor()
            cursor.execute(
                """
                CREATE TABLE data(key TEXT, activity TEXT, datalist TEXT)
                """,
            )
            db.commit()

    def save(self, data_headers, data_list, name) -> None:
        with self as db:
            db.connection.execute("""PRAGMA synchronous = EXTRA""")
            db.connection.execute("""PRAGMA journal_mode = WAL""")

            for row in data_list:
                modifiedlist = list(
                    map(lambda x, y: x.upper() + ": " + str(y), data_headers, row),
                )
                db.connection.executemany(
                    "INSERT INTO data VALUES(?,?,?)",
                    [(str(row[0]), name.upper(), str(modifiedlist))],
                )


class TsvManager(DBManager):
    def __init__(self, report_folder: pathlib.Path) -> None:
        db_folder: str = "_TSV Exports"

        super().__init__(db_folder=report_folder / db_folder)

    def __call__(self, name: str):
        self.db_file = self.db_folder / f"{name}.tsv"
        return self

    def create(self) -> None:
        pass

    def __enter__(self) -> codecs.StreamReaderWriter:
        self.connection = codecs.open(self.db_file, "a", "utf-8-sig")
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.connection.close()

    def save(self, name, data_headers, data_list) -> None:
        with self as file:
            tsv_writer = csv.writer(file, delimiter="\t")
            tsv_writer.writerow(data_headers)
            for i in data_list:
                tsv_writer.writerow(i)


@dataclass
class DBService:
    __slots__ = ["_report_folder", "_databases"]

    def __init__(self, report_folder: pathlib.Path) -> None:
        self._report_folder = report_folder
        self._databases = {}
        self._databases["kml"] = KmlDBManager(report_folder)
        self._databases["timeline"] = TimelineDBManager(report_folder)
        self._databases["tsv"] = TsvManager(report_folder)

        self._databases["kml"].create()
        self._databases["timeline"].create()
        self._databases["tsv"].create()

    def save(self, db_type: str, name: str, data_list: list[t.Any], data_headers):
        try:
            db = self._databases[db_type]
            if db_type == "tsv":
                db(name).save(name=name, data_list=data_list, data_headers=data_headers)
            else:
                db.save(name=name, data_list=data_list, data_headers=data_headers)
        except KeyError as err:
            raise DatabaseError(
                f"Database type {repr(db_type)} does not exists!"
            ) from err
