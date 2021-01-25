import fnmatch
import tarfile
from abc import ABC, abstractmethod
from pathlib import Path
from shutil import copyfile
from zipfile import ZipFile

from helpers.db import open_sqlite_db_readonly


class FileSeekerBase(ABC):

    _all_files = any
    _directory = Path()

    @abstractmethod
    def search(self, filepattern_to_search, return_on_first_hit=False):
        '''Returns a list of paths for files/folders that matched'''
        pass

    @abstractmethod
    def cleanup(self):
        '''close any open handles'''
        pass

    @abstractmethod
    def build_files_list(self):
        """Finds files in directory"""
        pass

    @property
    def directory(self):
        return self._directory

    @directory.setter
    def directory(self, directory):
        self._directory = Path(directory)

    @property
    def all_files(self):
        return self._all_files

    @all_files.setter
    def all_files(self, files):
        self._all_files = files


class FileSeekerDir(FileSeekerBase):
    def __init__(self, directory):
        self.directory = directory
        logfunc('Building files listing...')
        self.build_files_list(directory)
        logfunc(f'File listing complete - {len(self._all_files)} files')

    def build_files_list(self, directory):
        '''Populates all paths in directory into _all_files'''

        directory = directory or self.directory

        try:
            self.all_files = [file for file in Path(directory).rglob('**')]
        except Exception as ex:
            logfunc(f'Error reading {directory} ' + str(ex))

    def search(self, filepattern, return_on_first_hit=False):
        if return_on_first_hit:
            for item in self._all_files:
                if fnmatch.fnmatch(item, filepattern):
                    return [item]
            return []
        return fnmatch.filter(self._all_files, filepattern)


class FileSeekerItunes(FileSeekerBase):
    def __init__(self, directory, temp_folder):
        FileSeekerBase.__init__(self)
        self.directory = directory
        self.temp_folder = temp_folder

        logfunc('Building files listing...')
        self.build_files_list(directory)
        logfunc(f'File listing complete - {len(self._all_files)} files')

    def build_files_list(self, directory):
        '''Populates paths from Manifest.db files into _all_files'''

        directory = directory or self.directory

        try:
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
        except Exception as ex:
            logfunc(f'Error opening Manifest.db from {directory}, ' + str(ex))
            raise ex

    def search(self, filepattern, return_on_first_hit=False):
        pathlist = []
        matching_keys = fnmatch.filter(self._all_files, filepattern)
        for relative_path in matching_keys:
            hash_filename = self._all_files[relative_path]
            original_location = (
                Path(self.directory) / hash_filename[:2] / hash_filename
            )
            temp_location = Path(self.temp_folder) / relative_path

            try:
                temp_location.mkdir(parents=True, exist_ok=True)
                copyfile(original_location, temp_location)
                pathlist.append(temp_location)
            except Exception as ex:
                logfunc(f'Could not copy {original_location} to {temp_location} ' + str(ex))

        return pathlist


class FileSeekerTar(FileSeekerBase):
    def __init__(self, tar_file_path, temp_folder):
        self.is_gzip = tar_file_path.lower().endswith('gz')
        mode = 'r:gz' if self.is_gzip else 'r'
        self.tar_file = tarfile.open(tar_file_path, mode)
        self.temp_folder = temp_folder

    def search(self, filepattern, return_on_first_hit=False):
        pathlist = []
        for member in self.tar_file.getmembers():
            if fnmatch.fnmatch(member.name, filepattern):
                try:
                    full_path = Path(self.temp_folder) / member.name
                    if member.isdir():
                        full_path.mkdir(parents=True, exist_ok=True)
                    else:
                        if not full_path.parent.exists():
                            full_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(full_path, "wb") as fout:
                            fout.write(tarfile.ExFileObject(self.tar_file,
                                                            member).read())
                            fout.close()
                        os.utime(full_path, (member.mtime, member.mtime))
                    pathlist.append(full_path)
                except Exception as ex:
                    logfunc(f'Could not write file to filesystem, path was {member.name} ' + str(ex))
        return pathlist

    def cleanup(self):
        self.tar_file.close()


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
                    logfunc(f'Could not write file to filesystem, path was {member} ' + str(ex))
        return pathlist

    def cleanup(self):
        self.zip_file.close()
