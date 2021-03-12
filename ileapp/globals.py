import datetime
import logging
import sqlite3
from collections import UserDict, defaultdict
from io import FileIO
from pathlib import Path
from typing import Type, Union

from ileapp import VERSION as VERSION, __authors__ as authors
from ileapp.helpers.search import FileSeekerBase

logger = logging.getLogger(__name__)

THUMBNAIL_ROOT = '**/Media/PhotoData/Thumbnails/**'
MEDIA_ROOT = '**/Media'
THUMB_SIZE = 256, 256


class Device(UserDict):
    def table(self):
        return [[key, value] for key, value in self.data.items()]


def set_output_folder(output_folder):
    """Sets and creates output folders for the reports

    Args:
        output_folder (str or Path): output folder for reports
    """
    now = datetime.datetime.now()
    current_time = now.strftime('%Y-%m-%d_%A_%H%M%S')

    report_folder = (
        Path(output_folder) / f'iLEAPP_Reports_{current_time}'
    )

    temp_folder = report_folder / 'temp'
    log_folder = report_folder / 'Script Logs'
    log_folder.mkdir(parents=True, exist_ok=True)
    temp_folder.mkdir(parents=True, exist_ok=True)
    return report_folder, temp_folder, log_folder, temp_folder


class FileHandles(UserDict):

    def __init__(self) -> None:
        self.data = defaultdict(list)
        self._items = 0

    def __len__(self) -> int:
        return self._items

    def __setitem__(self, regex: str, file: str) -> None:
        print(file, self.data)
        self._items += 1
        p = Path(file)
        db = sqlite3.Connection
        file = FileIO

        try:
            db = sqlite3.connect(f'file:{p}?mode=ro', uri=True)
            cursor = db.cursor()
            page_size, = (
                cursor.execute('PRAGMA page_size').fetchone())
            page_count, = (
                cursor.execute('PRAGMA page_count').fetchone())

            if page_size * page_count < 20480:  # less then 20 MB
                db_mem = sqlite3.connect(':memory:')
                db_copy = db.backup(db_mem)
                db.close()
                db = db_copy

            self.data[regex].append(db)
        except (sqlite3.OperationalError, sqlite3.DatabaseError):
            file = open(p, 'rb')
            self.data[regex].append(file)
        except FileNotFoundError:
            raise FileNotFoundError(f'File {p} was not found!')

    def __getitem__(self, regex: str) -> Union[sqlite3.Connection, FileIO]:
        try:
            return self.data[regex]
        except KeyError:
            return KeyError(f'Regex {regex} has no files openned!')

    def __delitem__(self, regex: str):
        files = self.data.pop(regex, None)
        if files:
            if isinstance(files, list):
                [f.close for f in files]
            else:
                files.close()
            return True
        return False


def generate_program_header(input_path, num_to_process, num_of_categories):
    project = VERSION.split(' ')[0]
    version = VERSION.split(' ')[1]
    header = ('Procesing started. Please wait. This may take a '
              'few minutes...\n'
              '-----------------------------------------------------------'
              '---------------------------\n\n'
              f'{project} {version}: iLEAPP Logs, '
              'Events, and Properties Parser\n'
              'Objective: Triage iOS Full System Extractions.\n\n')

    for author in authors:
        header += f'By: {author[0]} | {author[2]} | {author[1]}\n'

    header += (f'\nArtifacts to parse: {num_to_process} in {num_of_categories} '
               'categories\n'
               f'File/Path Selected: {input_path}\n\n'
               '-----------------------------------------------------------'
               '---------------------------\n')
    return header


# Global Class
device = Device()

# Keeps track of open files
files = FileHandles()

# Keeps track of how many artifacts use each regex
# At zero, files for that regex are closed
regex = defaultdict(int)

# Global search object
seeker = Type[FileSeekerBase]

# Report Folder Base
report_folder = Union[Type[str], Type[Path]]
