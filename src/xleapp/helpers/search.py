from __future__ import annotations

import fnmatch
import logging
import os
import sqlite3
import tarfile
import typing as t

from abc import ABC, abstractmethod
from collections import UserDict, defaultdict
from functools import cached_property
from io import IOBase
from pathlib import Path
from zipfile import ZipFile

import magic

import xleapp.helpers.utils as utils

from xleapp.artifacts.regex import Regex
from xleapp.helpers.descriptors import Validator


logger_log = logging.getLogger("xleapp.logfile")
logger_process = logging.getLogger("xleapp.process")

if t.TYPE_CHECKING:
    BaseUserDict = UserDict[str, t.Any]
else:
    BaseUserDict = UserDict


class PathValidator(Validator):
    """Validates if a Pathlike object was set."""

    def validator(self, value: t.Any) -> Path:
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

    def validator(self, value: t.Any) -> None:
        """Validates this property

        Args:
            value: value attempting to be set

        Raises:
            TypeError: raises error if not sqlite3.Connection or IOBase object.

        Returns:
            None if value is :obj:`Path`.
        """
        if isinstance(value, Path):
            return None
        elif not isinstance(value, (sqlite3.Connection, IOBase)):
            raise TypeError(
                f"Expected {value!r} to be one of: string, Path, sqlite3.Connection"
                " or IOBase.",
            )


class InputPathValidation(Validator):
    def validator(self, value: t.Any) -> t.Any:
        if isinstance(value, str):
            value = Path(value).resolve()

        if isinstance(value, Path) and value.exists():
            if not value.is_dir():
                return magic.from_file(str(value), mime=True), value
            else:
                return "dir", value

        if not value.exists():
            raise FileNotFoundError(f"File/Folder {str(value)} not found!")
        raise TypeError(f"Expected {str(value)} to be one of: str or Path.")


class Handle:
    """Handles file objects.

    Attributes:
        file_handle: sets the file or database connection
        path: location of the file or database. Set separately to ensure the path can be
            resolved as early as possible.

    Args:
        found_file: Object of the file from searching.
        path: Path of the file

    Returns:
        sqlite3.Connection, IOBase, or Path object.
    """

    file_handle = HandleValidator()
    path = PathValidator()

    def __init__(self, found_file: t.Any, path: Path | None = None) -> None:
        self.path = path
        if isinstance(found_file, str):
            self.file_handle = Path(found_file)
        else:
            self.file_handle = found_file

    def __call__(self) -> sqlite3.Connection | IOBase | Path | None:
        return self.file_handle or self.path

    def __repr__(self) -> str:
        return f"<Handle file_handle={self.file_handle!r}, path={self.path!r}>"


class FileHandles(UserDict):
    """Container to hold file information for artifacts.

    Args:
        *args:
        **kwargs:

    Attributes:
        logged: keeps track of which regex strings have been logged. This ensures
            only one log out put per regex when evaluating each one.
    """

    logged: defaultdict = defaultdict(int)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(self, *args, **kwargs)
        self.default_factory = set

    def __len__(self) -> int:
        return sum(count for count in self.values())

    def add(self, regex: Regex, files, file_names_only: bool = False) -> None:
        """Adds files for each regex to be tracked

        Args:
            regex(SearchRegex): string used to find the files
            files: set of handles or paths to track
            file_names_only(bool): keep only file names/paths but no file objects.

        Raises:
            FileNotFoundError: raises error if matched file is not found
        """
        if self.logged[regex.regex] == 0:
            logger_process.info(f"\nFiles for {regex.regex} located at:")
        for item in files:
            file_handle: Handle
            path: Path = None
            extended_path: Path = None

            if isinstance(item, (Path, str)):
                path = Path(item).resolve()
            elif isinstance(item, Handle):
                path = Path(item.path).resolve()

            """
            If we have more then 10 files, then set only
            file names instead of `FileIO` or
            `sqlite3.connection` to save memory. Most artifacts
            probably have less then 5 files they will read/use.
            """

            if len(files) > 10 or file_names_only:
                file_handle = Handle(found_file=item, path=path)
            else:
                if path.drive.startswith("\\\\?\\"):
                    extended_path = Path(path)

                if path.is_dir():
                    file_handle = Handle(found_file=item, path=path)
                else:
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
                logger_process.info(f"    {file_handle.path}")
                self[regex].add(file_handle)

    def clear(self) -> None:
        """Resets the tracked files."""
        self.data = {}
        self.logged = set()

    def __getitem__(self, regex: Regex) -> set[Handle]:
        try:
            files = super().__getitem__(regex)
            for artifact_file in files:
                if isinstance(artifact_file, IOBase):
                    artifact_file.seek(0)
            return files
        except KeyError:
            raise KeyError(f"Regex {regex} has no files opened!")

    def __delitem__(self, regex: Regex) -> None:
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
        input_path: file or direction for the extraction
    """

    temp_folder: Path
    input_path: InputPathValidation = InputPathValidation()
    _all_files: t.Union[list[str], dict[str, str]] = []
    _file_handles = FileHandles()

    @abstractmethod
    def __call__(
        self,
        directory_or_file: Path | None,
        temp_folder: Path | None,
    ) -> t.Type[FileSeekerBase]:
        pass

    @abstractmethod
    def search(
        self,
        file_pattern_to_search: str,
    ) -> t.Iterator:
        """Returns a list of paths for files/folders that matched

        Args:
            file_pattern_to_search: :obj:`str` to search for files
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """close any open handles"""
        pass

    @abstractmethod
    def build_files_list(
        self,
        folder: t.Optional[t.Union[str, Path]],
    ) -> t.Union[tuple[list, list], list, dict]:
        """Builds a file list to search

        Args:
            folder: folder to get files from if required

        Returns:
            A list of files
        """
        pass

    @property
    @abstractmethod
    def priority(self) -> int:
        raise NotImplementedError(f"Need to set a priority for {self!r}")

    @property
    def all_files(self) -> t.Union[list[str], dict[str, str]]:
        """List of all files searched

        Returns:
            A list or a dictionary of files
        """
        return self._all_files

    @all_files.setter
    def all_files(self, files: t.Union[list[str], dict[str, str]]):
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

    @cached_property
    @abstractmethod
    def validate(self) -> bool:
        """Validates input for this seeker

        Returns:
            Returns True if validated or False if fails.
        """
        raise NotImplementedError(f"Need validate property for {self!r}!")


class FileSeekerDir(FileSeekerBase):
    """Searches directory for files."""

    def __call__(self, directory_or_file, temp_folder=None):
        self.input_path = Path(directory_or_file)
        if self.validate:
            logger_log.info("Building files listing...")
            sub_folders, files = self.build_files_list(directory_or_file)
            self.all_files.extend(sub_folders)
            self.all_files.extend(files)
            logger_log.info(f"File listing complete - {len(self._all_files)} files")
        return self

    def build_files_list(self, folder):
        sub_folders, files = [], []

        for item in os.scandir(folder):
            if item.is_dir():
                sub_folders.append(item.path)
            if item.is_file():
                files.append(item.path)

        for folder in list(sub_folders):
            sf, items = self.build_files_list(folder)
            sub_folders.extend(sf)
            files.extend(items)

        return sub_folders, files

    def search(self, file_pattern):
        return iter(fnmatch.filter(self.all_files, file_pattern))

    def cleanup(self) -> None:
        pass

    @property
    def priority(self) -> int:
        return 20

    @cached_property
    def validate(self) -> bool:
        mime, _ = self.input_path
        return mime == "dir"


class FileSeekerTar(FileSeekerBase):
    """Searches tar backup for files."""

    def __call__(self, directory_or_file, temp_folder):
        self.input_path = Path(directory_or_file)
        if self.validate:
            self.input_file = tarfile.open(directory_or_file, "r:*")
            self.temp_folder = Path(temp_folder)
        return self

    def search(self, file_pattern: str) -> t.Iterator[Path]:
        for member in self.build_files_list():
            if fnmatch.fnmatch(member.name, file_pattern):

                full_sanitize_name = utils.sanitize_file_path(str(member.name))
                if utils.is_platform_windows():
                    full_path = Path(f"\\\\?\\{self.temp_folder / full_sanitize_name}")
                else:
                    full_path = self.temp_folder / full_sanitize_name

                if not member.isdir():
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    full_path.write_bytes(
                        tarfile.ExFileObject(self.input_file, member).read(),
                    )
                yield full_path

    def cleanup(self) -> None:
        self.input_file.close()

    def build_files_list(self, folder=None) -> list[tarfile.TarInfo]:
        return self.input_file.getmembers()

    @cached_property
    def validate(self) -> bool:
        mime, _ = self.input_path
        # "inode/blockdevice" seems to be the file magic number on some iOS tar
        # extractions could manually pull the magic numbers instead of this for
        # tar file.
        return mime in [
            "application/x-gzip",
            "application/x-tar",
        ] or self.input_file.suffix in [".gz", ".tar", ".tar.gz"]

    @property
    def priority(self) -> int:
        return 20


class FileSeekerZip(FileSeekerBase):
    """Search backup zip file for files."""

    def __call__(
        self,
        directory_or_file,
        temp_folder,
    ):
        self.input_path = Path(directory_or_file)
        if self.validate:
            self.input_file = ZipFile(directory_or_file, "r")
            self.temp_folder = temp_folder
        return self

    def search(self, file_pattern: str):
        path_list: list[str] = []
        for member in self.build_files_list():
            if fnmatch.fnmatch(member, file_pattern):
                try:
                    extracted_path = (
                        # already replaces illegal chars with _ when exporting
                        self.input_file.extract(member, path=self.temp_folder)
                    )
                    path_list.append(extracted_path)
                except Exception:
                    member = member.lstrip("/")
        return iter(path_list)

    def build_files_list(self, folder=None):
        return self.input_file.namelist()

    def cleanup(self) -> None:
        self.input_file.close()

    @cached_property
    def validate(self) -> bool:
        mime, _ = self.input_path
        return mime == "application/zip" or self.input_path.suffix in [".zip"]

    @property
    def priority(self) -> int:
        return 20


class FileSearchProvider(BaseUserDict):
    """Search provider to control which kind of location is being searched

    Attributes:
        data: dictionary containing all the search providers
        _items: number of search providers
    """

    data: dict[str, FileSeekerBase]
    _items: int

    def __init__(self) -> None:
        self.data = {}
        self._items: int = 0

    def __len__(self) -> int:
        return self._items

    def register_builder(self, key: str, builder: FileSeekerBase) -> None:
        """Register a search builder

        Args:
            key: short name of search builder
            builder: object to perform the search
        """
        self._items = self._items + 1
        self.data[key] = builder

    def __call__(self, extraction_type: str, *, input_path: Path, **kwargs: t.Any):
        """Creates or returns the search provider

        Args:
            extraction_type(str): short name for seeker
            input_path(Path): path to search for files
            **kwargs: options for the search provider

        Raises:
            ValueError: raises error if builder has not been register

        Returns:
            FileSearchBase.
        """
        builder: t.Optional[FileSeekerBase] = self.data.get(extraction_type)

        if not builder:
            raise ValueError(extraction_type)
        return builder(directory_or_file=input_path, **kwargs)


search_providers = FileSearchProvider()
search_providers.register_builder("FS", FileSeekerDir())
search_providers.register_builder("TAR", FileSeekerTar())
search_providers.register_builder("ZIP", FileSeekerZip())
