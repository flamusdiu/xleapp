import fnmatch
import logging
import os
import sqlite3
import tarfile
from abc import ABC, abstractmethod
from collections import UserDict
from io import BufferedIOBase
from pathlib import Path
from shutil import copyfile
from typing import AnyStr, List, Tuple, Type, Union
from zipfile import ZipFile

from ileapp.helpers.db import open_sqlite_db_readonly

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Types
FileList = List[AnyStr]
SubFolders = List[AnyStr]


class FileHandles(UserDict):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(self, *args, **kwargs)
        self.default_factory = set
        self._items = 0

    def add(self, regex: str, files: list, file_names_only: bool = False) -> None:

        if self.get(regex):
            return

        for file in files:
            self._items += 1

            '''If we have more then 10 files, then set only
            file names instead of `FileIO` or
            `sqlite3.connection` to save memory. Most artifacts
            probably have less then 5 files they will read/use.
            '''

            if len(files) > 10 or file_names_only:
                self[regex].add(file)
                continue

            p = Path(file)
            try:
                db = sqlite3.connect(f'file:{p}?mode=ro', uri=True)
                cursor = db.cursor()
                (page_size,) = cursor.execute('PRAGMA page_size').fetchone()
                (page_count,) = cursor.execute('PRAGMA page_count').fetchone()

                if page_size * page_count < 20480:  # less then 20 MB
                    db_mem = sqlite3.connect(':memory:')
                    db.backup(db_mem)
                    db.close()
                    db = db_mem
                db.row_factory = sqlite3.Row
                self[regex].add(db)
            except (sqlite3.OperationalError, sqlite3.DatabaseError):
                fp = open(p, 'rb')
                self[regex].add(fp)
            except FileNotFoundError:
                raise FileNotFoundError(f'File {p} was not found!')

    def __getitem__(self, regex: str) -> Union[sqlite3.Connection, BufferedIOBase]:
        try:
            items = super().__getitem__(regex)

            for num, item in enumerate(items, start=1):
                if num == 1:
                    logger.info(
                        f'\nFiles for {regex} located at:',
                        extra={'flow': 'process_file'},
                    )
                if type(item) == sqlite3.Connection:
                    cur = item.cursor()
                    cur.execute("PRAGMA database_list")
                    rows = cur.fetchall()

                    logger.info(f'\t{rows[0][2]}', extra={'flow': 'process_file'})
                else:
                    logger.info(f'\t{item.name}', extra={'flow': 'process_file'})
                if isinstance(item, BufferedIOBase):
                    item.seek(0)
            return items
        except KeyError:
            raise KeyError(f'Regex {regex} has no files opened!')

    def __delitem__(self, regex: str):
        files = self.__dict__.pop(regex, None)
        if files:
            if isinstance(files, list):
                for f in files:
                    f.close()
                    self._items -= 1
            else:
                files.close()
                self._items -= 1
            return True
        return False

    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        if key not in self:
            self[key] = self.default_factory()
        return self[key]


class FileSeekerBase(ABC):

    _all_files = []
    _directory = Path()
    _file_handles = FileHandles()

    @abstractmethod
    def search(self, filepattern_to_search, return_on_first_hit=False) -> FileList:
        '''Returns a list of paths for files/folders that matched'''
        pass

    @abstractmethod
    def cleanup(self):
        '''close any open handles'''
        pass

    @abstractmethod
    def build_files_list(self, dir: Union[str, Path]) -> Tuple[SubFolders, FileList]:
        """Finds files in directory"""
        pass

    @property
    def directory(self) -> Path:
        return self._directory

    @directory.setter
    def directory(self, directory: Union[str, Path]):
        self._directory = Path(directory)

    @property
    def all_files(self) -> List[AnyStr]:
        return self._all_files

    @all_files.setter
    def all_files(self, files: List[AnyStr]):
        self._all_files = files

    @property
    def file_handles(self) -> FileHandles:
        return self._file_handles


class FileSeekerDir(FileSeekerBase):
    def __init__(self, directory, temp_folder=None) -> None:
        self.directory = directory
        logger.info('Building files listing...', extra={'flow': 'no_filter'})
        subfolders, files = self.build_files_list(directory)
        self.all_files.extend(subfolders)
        self.all_files.extend(files)
        logger.info(
            f'File listing complete - {len(self._all_files)} files',
            extra={'flow': 'no_filter'},
        )

    def build_files_list(self, dir) -> tuple((List[str], List[str])):
        '''Populates all paths in directory into _all_files'''

        subfolders, files = [], []

        for f in os.scandir(dir):
            if f.is_dir():
                subfolders.append(f.path)
            if f.is_file():
                files.append(f.path)

        for dir in list(subfolders):
            sf, f = self.build_files_list(dir)
            subfolders.extend(sf)
            files.extend(f)

        return subfolders, files

    def search(self, filepattern):
        return iter(fnmatch.filter(self.all_files, filepattern))

    def cleanup(self):
        pass


class FileSeekerItunes(FileSeekerBase):
    def __init__(self, directory, temp_folder):

        self.directory = directory
        self.temp_folder = temp_folder

        # logfunc('Building files listing...')
        self.build_files_list(directory)
        # logfunc(f'File listing complete - {len(self._all_files)} files')

    def build_files_list(self, dir):
        '''Populates paths from Manifest.db files into _all_files'''

        directory = dir or self.directory

        db = open_sqlite_db_readonly(Path(directory) / "Manifest.db")
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
            """
        )
        all_rows = cursor.fetchall()
        for row in all_rows:
            hash_filename = row[0]
            relative_path = row[1]
            self._all_files[relative_path] = hash_filename
        db.close()
        return [], []

    def search(self, filepattern, return_on_first_hit=False) -> List:
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
        self.is_gzip = directory.lower().endswith('gz')
        mode = 'r:gz' if self.is_gzip else 'r'
        self.tar_file = tarfile.open(directory, mode)
        self.temp_folder = temp_folder

    def search(self, filepattern, return_on_first_hit=False):
        pathlist = []
        for member in self.tar_file.getmembers():
            if fnmatch.fnmatch(member.name, filepattern):

                full_path = Path(self.temp_folder) / member.name
                if member.isdir():
                    full_path.mkdir(parents=True, exist_ok=True)
                else:
                    if not full_path.parent.exists():
                        full_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(full_path, "wb") as fout:
                        fout.write(tarfile.ExFileObject(self.tar_file, member).read())
                        fout.close()
                    os.utime(full_path, (member.mtime, member.mtime))
                pathlist.append(full_path)
        return iter(pathlist)

    def cleanup(self):
        self.tar_file.close()

    def build_files_list(self):
        """Tar files doe not build file list."""
        pass


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
                except Exception as ex:
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

    def create(self, key, **kwargs) -> Type[FileSeekerBase]:
        builder = self.data.get(key)
        if not builder:
            raise ValueError(key)
        return builder(**kwargs)


search_providers = FileSearchProvider()
search_providers.register_builder('FS', FileSeekerDir)
search_providers.register_builder('ITUNES', FileSeekerItunes)
search_providers.register_builder('TAR', FileSeekerTar)
search_providers.register_builder('ZIP', FileSeekerZip)
