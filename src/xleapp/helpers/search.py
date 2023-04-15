from __future__ import annotations

import abc
import collections
import fnmatch
import functools
import io
import logging
import os
import pathlib
import sqlite3
import tarfile
import typing as t

from zipfile import ZipFile

import magic
import xleapp.artifact.regex as regex
import xleapp.helpers.descriptors as descriptors
import xleapp.helpers.strings as strings
import xleapp.helpers.utils as utils


logger_log = logging.getLogger("xleapp.logfile")
logger_process = logging.getLogger("xleapp.process")

if t.TYPE_CHECKING:
    BaseUserDict = collections.UserDict[str, t.Any]
else:
    BaseUserDict = collections.UserDict


class PathValidator(descriptors.Validator):
    """Validates if a Pathlike object was set."""

    def validator(self, value: t.Any) -> pathlib.Path:
        """Validates this property

        Args:
            value: value attempting to be set

        Raises:
            TypeError: raises error if not Path or Pathlike object.

        Returns:
            :obj:`Path`.
        """
        if not isinstance(value, (pathlib.Path, os.PathLike, str)):
            raise TypeError(f"Expected {value!r} to be a Path or Pathlike object")
        return pathlib.Path(value).resolve()


class HandleValidator(descriptors.Validator):
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
        if isinstance(value, pathlib.Path):
            # Set as string to ensure 'None' is returned properly.
            return "None"
        elif not isinstance(value, (sqlite3.Connection, io.IOBase)):
            raise TypeError(
                f"Expected {value!r} to be one of: string, Path, sqlite3.Connection"
                " or IOBase.",
            )


class InputPathValidation(descriptors.Validator):
    def validator(self, value: t.Any) -> t.Any:
        if isinstance(value, str):
            value = pathlib.Path(value).resolve()

        if isinstance(value, pathlib.Path):
            if value.exists():
                if value.is_dir():
                    return "dir", value
                else:
                    return magic.from_file(str(value), mime=True), value
            else:
                raise FileNotFoundError(f"File/Folder {str(value)} not found!")
        else:
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

    def __init__(self, found_file: t.Any, path: pathlib.Path | None = None) -> None:
        self.path = path
        if isinstance(found_file, str):
            self.file_handle = pathlib.Path(found_file)
        else:
            self.file_handle = found_file

    def __call__(self) -> sqlite3.Connection | io.IOBase | pathlib.Path | None:
        return self.file_handle or self.path

    def __repr__(self) -> str:
        return f"<Handle file_handle={self.file_handle!r}, path={self.path!r}>"

    def __str__(self) -> str:
        return f"Handle {self.file_handle!r} of {self.path!r}"


class FileHandles(collections.UserDict):
    """Container to hold file information for artifacts.

    Args:
        *args:
        **kwargs:

    Attributes:
        logged: keeps track of which regex strings have been logged. This ensures
            only one log out put per regex when evaluating each one.
    """

    logged: collections.defaultdict = collections.defaultdict(int)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(self, *args, **kwargs)
        self.default_factory = set

    def __len__(self) -> int:
        return sum(count for count in self.values())

    def __repr__(self) -> str:
        return f"<FileHandles default_factory={self.default_factory}>"

    def add(self, regex: regex.Regex, files, file_names_only: bool = False) -> None:
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
            path: pathlib.Path = None
            extended_path: pathlib.Path = None

            if isinstance(item, (pathlib.Path, str)):
                path = pathlib.Path(item).resolve()
            elif isinstance(item, Handle):
                path = pathlib.Path(item.path).resolve()

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
                    extended_path = pathlib.Path(path)

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
                    except sqlite3.DatabaseError:
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

    def __getitem__(self, regex: regex.Regex) -> set[Handle]:
        try:
            files = super().__getitem__(regex)
            for artifact_file in files:
                if isinstance(artifact_file, io.IOBase):
                    artifact_file.seek(0)
            return files
        except KeyError:
            raise KeyError(f"Regex {regex} has no files opened!")

    def __delitem__(self, regex: regex.Regex) -> None:
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


class FileSeekerBase(abc.ABC):
    """Base class to search files

    Attributes:
        temp_folder: temporary folder to store files
        input_path: file or direction for the extraction
    """

    temp_folder: pathlib.Path
    input_path: InputPathValidation = InputPathValidation()
    _all_files: set = set()
    _file_handles = FileHandles()

    def __repr__(self) -> str:
        return (
            f"<{type(self).__name__} input_path={self.input_path!r} "
            f"priority={self.priority!r}>"
        )

    def __str__(self) -> str:
        name_lst = strings.split_camel_case(type(self).__name__)
        name = name_lst.pop()
        return (
            f"File Seeker ({name}) has the input path of {self.input_path!r} with "
            f"a priority {self.priority!r}"
        )

    @abc.abstractmethod
    def __call__(
        self,
        directory_or_file: pathlib.Path | None,
        temp_folder: pathlib.Path | None,
    ) -> t.Type[FileSeekerBase]:
        pass

    @abc.abstractmethod
    def search(
        self,
        file_pattern_to_search: str,
    ) -> t.Iterator:
        """Returns a list of paths for files/folders that matched

        Args:
            file_pattern_to_search: :obj:`str` to search for files
        """

    @abc.abstractmethod
    def cleanup(self) -> None:
        """close any open handles"""

    @abc.abstractmethod
    def build_files_list(
        self,
        folder: t.Optional[t.Union[str, pathlib.Path]],
    ) -> t.Union[tuple[list, list], list, dict]:
        """Builds a file list to search

        Args:
            folder: folder to get files from if required

        Returns:
            A list of files
        """

    @property
    @abc.abstractmethod
    def priority(self) -> int:
        raise NotImplementedError(f"Need to set a priority for {self!r}")

    @property
    def all_files(self) -> set:
        """Set of all files searched

        Returns:
            A Set of all files
        """
        return self._all_files

    @all_files.setter
    def all_files(self, files: set):
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

    @functools.cached_property
    @abc.abstractmethod
    def validate(self) -> bool:
        """Validates input for this seeker

        Returns:
            Returns True if validated or False if fails.
        """


class FileSeekerDir(FileSeekerBase):
    """Searches directory for files."""

    def __call__(self, directory_or_file, temp_folder=None):
        self.input_path = pathlib.Path(directory_or_file)
        if self.validate:
            logger_log.info("Building files listing...")
            self.all_files = self.build_files_list(directory_or_file)
            logger_log.info(f"File listing complete - {len(self.all_files)} files")
        return self

    def build_files_list(self, folder):
        folders, files = set(), set()

        for root, sub_folders, fls in os.walk(folder):
            for folder in sub_folders:
                folders.add(f"{root}\\{folder}")

            for f in fls:
                files.add(f"{root}\\{f}")

        return folders | files

    def search(self, file_pattern):
        return iter(fnmatch.filter(self.all_files, file_pattern))

    def cleanup(self) -> None:
        pass

    @property
    def priority(self) -> int:
        return 20

    @functools.cached_property
    def validate(self) -> bool:
        mime, _ = self.input_path
        return mime == "dir"


class FileSeekerTar(FileSeekerBase):
    """Searches tar backup for files."""

    def __call__(self, directory_or_file, temp_folder):
        self.input_path = pathlib.Path(directory_or_file)
        if self.validate:
            self.input_file = tarfile.open(directory_or_file, "r:*")
            self.temp_folder = pathlib.Path(temp_folder)
        return self

    def search(self, file_pattern: str) -> t.Iterator[pathlib.Path]:
        for member in self.build_files_list():
            if fnmatch.fnmatch(member.name, file_pattern):
                full_sanitize_name = utils.sanitize_file_path(str(member.name))
                if utils.is_platform_windows():
                    full_path = pathlib.Path(
                        f"\\\\?\\{self.temp_folder / full_sanitize_name}"
                    )
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

    @functools.cached_property
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
        self.input_path = pathlib.Path(directory_or_file)
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

    @functools.cached_property
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

    def __call__(
        self, extraction_type: str, *, input_path: pathlib.Path, **kwargs: t.Any
    ):
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
