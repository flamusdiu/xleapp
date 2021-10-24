import fnmatch
import logging
import os
import sqlite3
import tarfile
import typing as t

from abc import ABC, abstractmethod
from collections import UserDict
from io import IOBase
from pathlib import Path
from shutil import copyfile
from zipfile import ZipFile

from xleapp.helpers.descriptors import Validator

from .db import open_sqlite_db_readonly
from .utils import is_platform_windows


logger_log = logging.getLogger("xleapp.logfile")
logger_process = logging.getLogger("xleapp.process")


class PathValidator(Validator):
    def validator(self, value):
        if not isinstance(value, (Path, os.PathLike, str)):
            raise TypeError(f"Expected {value!r} to be a Path or Pathlike object")
        return value.resolve()


class HandleValidator(Validator):
    def validator(self, value) -> None:
        if isinstance(value, (str, Path)):
            return None
        elif not isinstance(value, (sqlite3.Connection, IOBase)):
            raise TypeError(
                f"Expected {value!r} to be one of: string, Path, sqlite3.Connection"
                " or IOBase.",
            )


class Handle:
    file_handle = HandleValidator()
    path = PathValidator()

    def __init__(self, found_file: t.Any, path: Path = None) -> None:
        self.path = path
        self.file_handle = found_file

    def __call__(self):
        return self.file_handle or self.path


class FileHandles(UserDict):
    logged: list = []

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(self, *args, **kwargs)
        self.default_factory = set

    def __len__(self) -> int:
        return sum(count for count in self.values())

    def add(self, regex: str, files: list, file_names_only: bool = False) -> None:

        if self.get(regex):
            return

        for item in files:
            file_handle = None
            path = Path(item.resolve())

            """
            If we have more then 10 files, then set only
            file names instead of `FileIO` or
            `sqlite3.connection` to save memory. Most artifacts
            probably have less then 5 files they will read/use.
            """

            if len(files) > 10 or file_names_only:
                file_handle = Handle(found_file=item, path=path)
            else:
                if item.drive.startswith("\\\\?\\"):
                    extended_path = Path(item)

                try:
                    db = sqlite3.connect(
                        f"file:{path}?mode=ro",
                        uri=True,
                        check_same_thread=False,
                    )
                    db.row_factory = sqlite3.Row
                    file_handle = Handle(found_file=db, path=path)
                except (sqlite3.OperationalError, sqlite3.DatabaseError, TypeError):
                    fp = open(extended_path, "rb")
                    file_handle = Handle(found_file=fp, path=path)
                except FileNotFoundError:
                    raise FileNotFoundError(f"File {path!r} was not found!")
            if file_handle:
                self[regex].add(file_handle)

    def __getitem__(self, regex: str) -> set[Handle]:
        try:
            files = super().__getitem__(regex)

            for num, file in enumerate(files, start=1):
                if regex not in self.logged:
                    if num == 1:
                        logger_process.info(f"\nFiles for {regex} located at:")

                    logger_process.info(f"    {file.path}")
                    self.logged.append(regex)

                if isinstance(file, IOBase):
                    file.seek(0)
            return files
        except KeyError:
            raise KeyError(f"Regex {regex} has no files opened!")

    def __delitem__(self, regex: str) -> None:
        files = self.__dict__.pop(regex, None)
        if files:
            if isinstance(files, list):
                for f in files:
                    f.close()
            else:
                files.close()

    def __missing__(self, key: str) -> set[Handle]:
        if self.default_factory is None:
            raise KeyError(key)
        if key not in self:
            self[key] = self.default_factory()
        return self[key]


class FileSeekerBase(ABC):

    temp_folder: Path
    _all_files: list[str] = []
    _directory: Path
    _file_handles = FileHandles()

    @abstractmethod
    def search(
        self,
        filepattern_to_search: str,
        return_on_first_hit: bool = False,
    ) -> t.Iterator[t.Any]:
        """Returns a list of paths for files/folders that matched"""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """close any open handles"""
        pass

    @abstractmethod
    def build_files_list(
        self, folder: t.Optional[t.Union[str, Path]]
    ) -> t.Union[tuple[list, list], list]:
        """Finds files in directory"""
        pass

    @property
    def directory(self) -> Path:
        return self._directory

    @directory.setter
    def directory(self, directory: t.Union[str, Path]):
        self._directory = Path(directory)

    @property
    def all_files(self) -> list[str]:
        return self._all_files

    @all_files.setter
    def all_files(self, files: list[str]):
        self._all_files = files

    @property
    def file_handles(self) -> FileHandles:
        return self._file_handles


class FileSeekerDir(FileSeekerBase):
    def __init__(self, directory, temp_folder=None):
        self.directory = Path(directory)
        logger_log.info("Building files listing...")
        subfolders, files = self.build_files_list(directory)
        self.all_files.extend(subfolders)
        self.all_files.extend(files)
        logger_log.info(f"File listing complete - {len(self._all_files)} files")

    def build_files_list(self, folder):
        """Populates all paths in directory into _all_files"""

        subfolders, files = [], []

        for item in os.scandir(folder):
            if item.is_dir():
                subfolders.append(item.path)
            if item.is_file():
                files.append(item.path)

        for folder in list(subfolders):
            sf, items = self.build_files_list(folder)
            subfolders.extend(sf)
            files.extend(items)

        return subfolders, files

    def search(self, filepattern, return_on_first_hit=False):
        return iter(fnmatch.filter(self.all_files, filepattern))

    def cleanup(self):
        pass


class FileSeekerItunes(FileSeekerBase):
    def __init__(self, directory, temp_folder) -> None:

        self.directory = Path(directory)
        self.temp_folder = Path(temp_folder)

        self.build_files_list()

    def build_files_list(self, folder=None) -> list:
        """Populates paths from Manifest.db files into _all_files"""

        directory = self.directory

        db = open_sqlite_db_readonly(directory / "Manifest.db")
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT
            fileID,
            relativePath
            FROM
            Files
            WHERE
            flags=1
            """,
        )
        all_rows = cursor.fetchall()
        for row in all_rows:
            hash_filename = row[0]
            relative_path = row[1]
            self._all_files[relative_path] = hash_filename
        db.close()

        # does not return any values for this FileSeeker
        return []

    def search(self, filepattern, return_on_first_hit=False):
        pathlist = []
        matching_keys = fnmatch.filter(self._all_files, filepattern)
        for relative_path in matching_keys:
            hash_filename = self._all_files[relative_path]
            original_location = Path(self.directory) / hash_filename[:2] / hash_filename
            temp_location = Path(self.temp_folder) / relative_path

            temp_location.mkdir(parents=True, exist_ok=True)
            copyfile(original_location, temp_location)
            pathlist.append(temp_location)

        return iter(pathlist)


class FileSeekerTar(FileSeekerBase):
    def __init__(self, directory, temp_folder):
        self.is_gzip = Path(directory).suffix == ".gz"
        mode = "r:gz" if self.is_gzip else "r"
        self.tar_file = tarfile.open(directory, mode)
        self.temp_folder = Path(temp_folder)

    def search(self, filepattern, return_on_first_hit=False):
        for member in self.build_files_list():
            if fnmatch.fnmatch(member.name, filepattern):

                if is_platform_windows():
                    full_path = Path(f"\\\\?\\{self.temp_folder / member.name}")
                else:
                    full_path = self.temp_folder / member.name

                if not member.isdir():
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    full_path.write_bytes(
                        tarfile.ExFileObject(self.tar_file, member).read(),
                    )
                    os.utime(full_path, (member.mtime, member.mtime))
                yield full_path

    def cleanup(self):
        self.tar_file.close()

    def build_files_list(self) -> list[tarfile.TarInfo]:
        return self.tar_file.getmembers()


class FileSeekerZip(FileSeekerBase):
    def __init__(self, zip_file_path, temp_folder):
        self.zip_file = ZipFile(zip_file_path)
        self.name_list = self.zip_file.namelist()
        self.temp_folder = temp_folder

    def search(self, filepattern, return_on_first_hit=False):
        pathlist = []
        for member in self.name_list:
            if fnmatch.fnmatch(member, filepattern):
                try:
                    extracted_path = (
                        # already replaces illegal chars with _ when exporting
                        self.zip_file.extract(member, path=self.temp_folder)
                    )
                    pathlist.append(extracted_path)
                except Exception:
                    member = member.lstrip("/")
                    # logfunc(f'Could not write file to filesystem, path was {member} ' + str(ex))
        return iter(pathlist)

    def cleanup(self):
        self.zip_file.close()


class FileSearchProvider(UserDict):
    def __init__(self) -> None:
        self.data = {}
        self._items = 0

    def __len__(self) -> int:
        return self._items

    def register_builder(self, key, builder) -> None:
        self._items = self._items + 1
        self.data[key] = builder

    def create(self, key, **kwargs) -> FileSeekerBase:
        builder = self.data.get(key)
        if not builder:
            raise ValueError(key)
        return builder(**kwargs)


search_providers = FileSearchProvider()
search_providers.register_builder("FS", FileSeekerDir)
search_providers.register_builder("ITUNES", FileSeekerItunes)
search_providers.register_builder("TAR", FileSeekerTar)
search_providers.register_builder("ZIP", FileSeekerZip)
