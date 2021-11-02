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

if t.TYPE_CHECKING:
    BaseUserDict = UserDict[str, t.Any]
else:
    BaseUserDict = UserDict


class PathValidator(Validator):
    """Validates if a Pathlike object was set."""

    def validator(self, value) -> Path:
        """Validates this property

        Args:
            value: value attempting to be set

        Raises:
            TypeError: raises error if not Path or Pathlike object.

        Returns:
            :obj:`Path`.
        """
        if not isinstance(value, (Path, os.PathLike, str)):
            raise TypeError(f"Expected {value!r} to be a Path or Pathlike object")
        return Path(value).resolve()


class HandleValidator(Validator):
    """Ensures only sqlite3.Connection or IOBase is set."""

    def validator(self, value) -> None:
        """Validates this property

        Args:
            value: value attempting to be set

        Raises:
            TypeError: raises error if not sqlite3.Connection or IOBase object.

        Returns:
            :obj:`Path`.
        """
        if isinstance(value, Path):
            return None
        elif not isinstance(value, (sqlite3.Connection, IOBase)):
            raise TypeError(
                f"Expected {value!r} to be one of: string, Path, sqlite3.Connection"
                " or IOBase.",
            )


class Handle:
    """Handles file objects.

    Attributes:
        file_handle: sets the file or database connection
        path: location of the file or database. Set seperatly to ensure the path can be
            resolved as early as possible.

    Args:
        found_file: Object of the file from searching.
        path: Path of the file

    Returns:
        sqlite3.Connection, IOBase, or Path object.
    """

    file_handle = HandleValidator()
    path = PathValidator()

    def __init__(self, found_file: t.Any, path: Path = None) -> None:
        self.path = path
        if isinstance(found_file, str):
            self.file_handle = Path(found_file)
        else:
            self.file_handle = found_file

    def __call__(self) -> t.Union[HandleValidator, PathValidator]:
        return self.file_handle or self.path


class FileHandles(UserDict):
    """Container to hold file information for artifacts.

    Args:
        *args:
        **kwargs:

    Attributes:
        logged: keeps track of which regex strings have been logged. This ensures
            only one log out put per regex when evaluating each one.
    """

    logged: set[str] = set()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(self, *args, **kwargs)
        self.default_factory = set

    def __len__(self) -> int:
        return sum(count for count in self.values())

    def add(
        self,
        regex: str,
        files: t.Union[set[Handle], set[Path]],
        file_names_only: bool = False,
    ) -> None:
        """Adds files for each regex to be tracked

        Args:
            regex: string used to find the files
            files: set of handels or paths to track
            file_names_only: keep only file names/paths but no file objects.
        """
        for item in files:
            file_handle: Handle
            path: t.Optional[Path] = None

            if isinstance(item, (Path, str)):
                path = Path(item)
            elif isinstance(item, Handle):
                path = Path(item.path)

            if path:
                path = path.resolve()

            """
            If we have more then 10 files, then set only
            file names instead of `FileIO` or
            `sqlite3.connection` to save memory. Most artifacts
            probably have less then 5 files they will read/use.
            """

            extended_path: t.Optional[Path] = None
            if len(files) > 10 or file_names_only:
                file_handle = Handle(found_file=item, path=path)
            else:
                if path.drive.startswith("\\\\?\\"):
                    extended_path = Path(path)

                try:
                    db = sqlite3.connect(
                        f"file:{path}?mode=ro",
                        uri=True,
                    )
                    cursor = db.cursor()
                    # This will fail if not a database file
                    cursor.execute("PRAGMA page_count").fetchone()
                    db.row_factory = sqlite3.Row
                    file_handle = Handle(found_file=db, path=path)
                except (sqlite3.DatabaseError):
                    if extended_path:
                        fp = open(extended_path, "rb")
                    else:
                        fp = open(path, "rb")
                    file_handle = Handle(found_file=fp, path=path)
                except FileNotFoundError:
                    raise FileNotFoundError(f"File {path!r} was not found!")
            if file_handle:
                self[regex].add(file_handle)

    def clear(self) -> None:
        """Resets the tracked files."""
        self.data = {}
        self.logged = set()

    def __getitem__(self, regex: str) -> set[Handle]:
        try:
            files = super().__getitem__(regex)

            for num, artifact_file in enumerate(files, start=1):
                if regex not in self.logged:
                    if num == 1:
                        logger_process.info(f"\nFiles for {regex} located at:")

                    logger_process.info(f"    {artifact_file.path}")
                    self.logged.add(regex)

                if isinstance(artifact_file, IOBase):
                    artifact_file.seek(0)
            return files
        except KeyError:
            raise KeyError(f"Regex {regex} has no files opened!")

    def __delitem__(self, regex: str) -> None:
        files = self.__dict__.pop(regex, None)
        if files:
            if isinstance(files, list):
                for artifact_file in files:
                    artifact_file.close()
            else:
                files.close()

    def __missing__(self, key: str) -> set[Handle]:
        if self.default_factory is None:
            raise KeyError(key)
        if key not in self:
            self[key] = self.default_factory()
        return self[key]


class FileSeekerBase(ABC):
    """Base class to search files

    Attributes:
        temp_folder: temporary folder to store files
    """

    temp_folder: Path
    _all_files: list[str] = []
    _directory: Path
    _file_handles = FileHandles()

    def __init__(self, *args, **kwargs) -> None:
        pass

    @abstractmethod
    def search(self, filepattern_to_search: str) -> t.Iterator[Path]:
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
        """Builds a file list to search

        Args:
            folder: folder to get files from if required

        Returns:
            A list of files
        """
        pass

    @property
    def directory(self) -> Path:
        """Directory to search

        Returns:
            The path to directory
        """
        return self._directory

    @directory.setter
    def directory(self, directory: t.Union[str, Path]):
        self._directory = Path(directory)

    @property
    def all_files(self) -> list[str]:
        """List of all files searched

        Returns:
            A list of files
        """
        return self._all_files

    @all_files.setter
    def all_files(self, files: list[str]):
        self._all_files = files

    @property
    def file_handles(self) -> FileHandles:
        """File handles and path found per regex

        Returns:
            A list of files or paths
        """
        return self._file_handles

    def clear(self) -> None:
        """Clears the list of file handles"""
        self.file_handles.clear()


class FileSeekerDir(FileSeekerBase):
    """Searches directory for files."""

    def __init__(self, directory, temp_folder=None):
        self.directory = Path(directory)
        logger_log.info("Building files listing...")
        subfolders, files = self.build_files_list(directory)
        self.all_files.extend(subfolders)
        self.all_files.extend(files)
        logger_log.info(f"File listing complete - {len(self._all_files)} files")

    def build_files_list(self, folder):
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

    def cleanup(self) -> None:
        pass


class FileSeekerItunes(FileSeekerBase):
    """Searches iTunes Backup for files."""

    def __init__(
        self,
        directory: t.Union[str, Path],
        temp_folder: t.Union[str, Path],
    ) -> None:

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

    def search(self, filepattern):
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
    """Searches tar backup for files."""

    def __init__(self, directory, temp_folder):
        self.is_gzip = Path(directory).suffix == ".gz"
        mode = "r:gz" if self.is_gzip else "r"
        self.tar_file = tarfile.open(directory, mode)
        self.temp_folder = Path(temp_folder)

    def search(self, filepattern: str) -> t.Iterator[Path]:
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

    def cleanup(self) -> None:
        self.tar_file.close()

    def build_files_list(self, folder=None) -> list[tarfile.TarInfo]:
        return self.tar_file.getmembers()


class FileSeekerZip(FileSeekerBase):
    """Search backup zip file for files."""

    def __init__(
        self,
        zip_file_path: t.Union[str, Path],
        temp_folder: Path,
    ) -> None:
        self.zip_file = ZipFile(zip_file_path)
        self.name_list = self.zip_file.namelist()
        self.temp_folder = temp_folder

    def search(
        self,
        filepattern: str,
    ) -> t.Iterator[str]:
        pathlist: list[str] = []
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

    def cleanup(self) -> None:
        self.zip_file.close()


class FileSearchProvider(BaseUserDict):
    """Search provider to control which kind of location is being searched

    Attributes:
        data: dictionary containing all the search providers
        _items: number of search providers
    """

    data: dict[str, t.Type[FileSeekerBase]]
    _items: int

    def __init__(self) -> None:
        self.data = {}
        self._items: int = 0

    def __len__(self) -> int:
        return self._items

    def register_builder(self, key: str, builder) -> None:
        """Register a search builder

        Args:
            key: short name of search builder
            builder: object to perform the search
        """
        self._items = self._items + 1
        self.data[key] = builder

    def create(self, key: str, **kwargs: t.Any):
        """Creates or returns the search provider

        Args:
            key: short name for the file seeker
            **kwargs: options for the search provider

        Raises:
            ValueError: raises error if builder has not been register

        Returns:
            FileSearchBase.
        """
        builder: t.Optional[t.Type[FileSeekerBase]] = self.data.get(key)

        if not builder:
            raise ValueError(key)
        return builder(**kwargs)


search_providers = FileSearchProvider()
search_providers.register_builder("FS", FileSeekerDir)
search_providers.register_builder("ITUNES", FileSeekerItunes)
search_providers.register_builder("TAR", FileSeekerTar)
search_providers.register_builder("ZIP", FileSeekerZip)
