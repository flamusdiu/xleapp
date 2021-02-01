import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Union, List, Optional

import ileapp.artifacts.helpers.html_report as artifact_report
from ileapp.helpers.decorators import timer
from ileapp.html_report import Icon

logger = logging.getLogger(__name__)


class WebIcon:
    """Descriptor ensuring 'web_icon' type
    """
    def __set_name__(self, owner, name):
        self.name = str(name)

    def __get__(self, obj, type=Icon) -> object:
        return obj.__dict__.get(self.name) or Icon.ALERT_TRIANGLE

    def __set__(self, obj, value) -> None:
        if isinstance(value, Icon) or isinstance(value, WebIcon):
            obj.__dict__[self.name] = value
        else:
            raise TypeError(
                f"Got {type(value)} instead of {type(Icon)}! "
                f"Error setting Web Icon on {str(obj)}!"
            )


class SearchDirs:
    """Descriptor enuring 'search_dirs" type
    """
    def __set_name__(self, owner, name):
        self.name = str(name)

    def __get__(self, obj, type=None) -> list:
        return obj.__dict__.get(self.name) or []

    def __set__(self, obj, value) -> None:
        if isinstance(value, str):
            obj.__dict__[self.name] = [value]
        elif isinstance(value, tuple):
            obj.__dict__[self.name] = [*value]
        elif isinstance(value, SearchDirs) or isinstance(value, list):
            obj.__dict__[self.name] = value
        else:
            raise TypeError(
                f"Error setting search dirs on {str(obj)}! "
                f"Type is {type(value)} instead of list, tuple "
                f"or str!"
            )


class FilesFound:
    """Descriptor ensuring 'files_found" type
    """
    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, type=None) -> Union[list, str]:
        value = obj.__dict__[self.name]
        if (isinstance(value, list)
                and len(value) == 1):
            return value[0]
        return value

    def __set__(self, obj, value) -> None:
        if isinstance(value, str):
            obj.__dict__[self.name] = [value]
        elif isinstance(value, FilesFound) or isinstance(value, list):
            obj.__dict__[self.name] = value
        else:
            raise TypeError(
                f"Error setting files found! Expected list or str! "
                f"Got {type(value)} instead!"
            )


@dataclass
class _AbstractBase:
    name: str = field(init=False)


@dataclass
class _AbstractArtifactDefaults:
    category: str = field(init=False, default='None')
    _core_artifact: bool = field(init=False, default=False)
    description: str = field(init=False, default='')
    files_found: List[str] = field(init=False, repr=False, default=FilesFound())
    generate_report: bool = field(init=False, default=True)
    report_headers: tuple = field(init=False, default=('Key', 'Values'))
    _long_running_process: bool = field(init=False, default=False)
    search_dirs: List[str] = field(init=False, default=SearchDirs())
    web_icon: Icon = field(init=False, default=WebIcon())


@dataclass
class AbstractArtifact(ABC, _AbstractArtifactDefaults, _AbstractBase):
    """Abstract class for creating Artifacts
    """
    __slots__ = '__dict__'

    def __post_init__(self):
        if self.generate_report:
            self.html_report = artifact_report.ArtifactHtmlReport

    @timer
    @abstractmethod
    def get(self, seeker):
        """Gets artifacts located in `files_found` params by the
        `seeker`. It saves should save the report in `report_folder`.

        Args:
            files_found (tuple): list of files found
                by `seeker`
            report_folder (str): location of the `report_folder` to save
                report of artifact
            seeker (FileSeekerBase): object to search for files
        """
        print("Needs to implement AbastractArtifact's get() method!")

    @property
    def data(self):
        """list: data found per artifact
        """
        return self._data

    @data.setter
    def data(self, data):
        self.html_report.data = data
        self._data = data

    @property
    def processing_time(self):
        return self._processing_time

    @processing_time.setter
    def processing_time(self, time):
        self._processing_time = time

    def report(self):
        if self.generate_report is False:
            logger.error(f'Report not generated for {self.name}! Artifact '
                         f'marked for no report generation. Check artifact\'s '
                         f'\'generate_report\' attribute.')
            return False
        self.html_report.report(self.files_found)
        return True

    @classmethod
    def open_file(props, file, func):
        """Opens a file and saves the handel

        Args:
            props (Props): global property object
            file (str or Path): Path to file to open
            func (function): Function to open file. Should accept a file path
                and return a file handle.

        Returns:
            handle: file handle returned by function
        """
        file = Path(file)

        if file.exists():
            opened = func(file)

            if opened:
                props.run_time_info['open_files'].update(
                    {
                        'name': str(file),
                        'handle': opened
                    }
                )
        return opened

    @classmethod
    def close_file(props, file):
        """Closes a file opened

        Args:
            props (Props): global property object
            file (str or Path): file to be closed

        Returns:
            bool: returns success of closure
        """
        file = Path(file)

        if str(file) in props.run_time_info['open_files']:
            handle = props.run_time_info['open_files'][str(file)]
            closed = handle.close()
        return closed or False


class core_artifact:
    def __init__(self, cls):
        self.cls = cls

    def __call__(self):
        if issubclass(self.cls, AbstractArtifact):
            setattr(self.cls, '_core_artifact', True)
            return self.cls()
        else:
            raise AttributeError(
                f'Class object {str(self.cls)} is an Artifact! '
                f'Error setting property \'core_artifact\' on class!'
            )


class long_running_process:
    def __init__(self, cls):
        self.cls = cls

    def __call__(self):
        if issubclass(self.cls, AbstractArtifact):
            setattr(self.cls, '_long_running_process', True)
            return self.cls()
        else:
            raise AttributeError(
                f'Class object {str(self.cls)} is an Artifact! '
                f'Error setting property \'long_running_process\' on class!'
            )
