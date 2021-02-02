import functools
import importlib
import inspect
import io
import logging
import os
import traceback
from abc import ABC, abstractmethod
from collections import OrderedDict, defaultdict, namedtuple
from dataclasses import dataclass, field
from pathlib import Path
from textwrap import TextWrapper
from typing import List, Union

import ileapp.artifacts.helpers.html_report as artifact_report
import prettytable
from ileapp.helpers import is_platform_windows
from ileapp.helpers.decorators import timer
from ileapp.helpers.search_files import (FileSeekerDir, FileSeekerItunes,
                                         FileSeekerTar, FileSeekerZip)
from ileapp.html_report import Icon

logger = logging.getLogger(__name__)

__all__ = [
    'AbstractArtifact',
    'generate_artifact_table',
    'generate_artifact_path_list',
    'crunch_core_artifacts',
    'crunch_core_artifacts',
    'select'
    'artifact_list'
]

# Setup named tuple to hold each artifact
Artifact = namedtuple('Artifact', ['name', 'cls'])
Artifact.__doc__ += ': Loaded forensic artifact'
Artifact.cls.__doc__ = 'Artifact object class'
Artifact.name.__doc__ = 'Artifact short name'


class Artifacts(OrderedDict):
    """List of artifacts installed
    """

    def __init__(self):
        super().__init__(self)

    def __setitem__(self, index, value) -> None:
        if isinstance(index, str) and isinstance(value, Artifact):
            super().__setitem__(index, value)
        else:
            raise TypeError(
                f"Error adding {{{str(index)}: {str(value)}}} to {self.name}! "
                f"Incorrect type for name or class not {type(Artifact)}"
            )

    def __str__(self) -> str:
        return f"Artifacts[{', '.join([name for name, artifact in self.items()])}]"


def _build_artifact_list() -> Artifacts:
    """Generates a List of Artifacts installed

    Returns:
        Artifacts: dictionary of artifacts with short names as keys
    """
    logger.debug('Generating artifact lists from file system...')
    module_dir = Path(importlib.util.find_spec(__name__).origin).parent
    artifact_list = Artifacts()
    for it in module_dir.glob('*.py'):
        if (it.suffix == '.py' and it.stem not in ['__init__']):
            module_name = f'{__name__}.{it.stem}'
            module = importlib.import_module(module_name, inspect.isfunction)
            module_members = inspect.getmembers(module, inspect.isclass)
            for name, cls in module_members:
                if (not str(cls.__module__).endswith('Artifact')
                        and str(cls.__module__).startswith(__name__)
                        and not inspect.isabstract(cls)):

                    artifact_obj = cls()
                    tmp_artifact = Artifact(
                        cls=artifact_obj,
                        name=artifact_obj.name
                    )
                    artifact_list.update({name: tmp_artifact})

    # sort the artifact list
    tmp_artifact_list = sorted(list(artifact_list.items()))
    artifact_list.clear()
    artifact_list.update(tmp_artifact_list)

    logger.debug(f'Artifacts loaded: { len(artifact_list) }')
    return artifact_list


def generate_artifact_path_list(artifacts):
    """Generates path file for usage with Autopsy
    """
    logger.info('Artifact path list generation started.')

    with open('path_list.txt', 'w') as paths:
        regex_list = []
        for artifact in artifacts:
            if isinstance(artifact.search_dirs, tuple):
                [regex_list.append(item) for item in artifact.search_dirs]
            else:
                regex_list.append(artifact.search_dirs)
        # Create a single list removing duplications
        ordered_regex_list = '\n'.join(set(regex_list))
        logger.info(ordered_regex_list)
        paths.write(ordered_regex_list)

        logger.info('Artifact path list generation completed')


def build_search_regex_list(search_list) -> list:
    search_regexes = defaultdict(list)
    for name in search_list:
        artifact = props.installed_artifacts[name]
        if ((isinstance(artifact.cls.search_dirs, list)
                or isinstance(artifact.cls.search_dirs, tuple))
                and artifact.cls.core_artifact is False):
            for regex in artifact.cls.search_dirs:
                search_regexes[regex].append(name)
        else:
            search_regexes[artifact.cls.search_dirs].append(name)

    return search_regexes


def generate_artifact_table(artifacts):
    """Generates artifact list table.
    """
    headers = ["Short Name", "Full Name", "Search Regex"]
    wrapper = TextWrapper(expand_tabs=False,
                          replace_whitespace=False,
                          width=60)
    output_table = prettytable.PrettyTable(headers, align='l')
    output_table.hrules = prettytable.ALL
    output_file = Path('artifact_table.txt')

    logger.info('Artifact table generation started.')

    with open(output_file, 'w') as paths:
        for key, val in artifacts:
            shortName = key
            fullName = val.cls.name
            searchRegex = val.cls.search_dirs
            if isinstance(searchRegex, tuple):
                searchRegex = '\n'.join(searchRegex)
            output_table.add_row([shortName,
                                  fullName,
                                  wrapper.fill(searchRegex)])
        paths.write(output_table.get_string(title='Artifact List',
                                            sortby='Short Name'))
    logger.info(f'Table saved to: {output_file}')
    logger.info('Artifact table generation completed')


def crunch_core_artifacts(extracttype, seeker, input_path, output_folder):
    for name, artifact in props.core_artifacts.items():
        # Now ready to run
        # Special processing for iTunesBackup Info.plist as it is a
        # separate entity, not part of the Manifest.db. Seeker won't find it
        if name == 'ITunesBackupInfo':
            if extracttype == 'itunes':
                info_plist_path = input_path / 'Info.plist'
                if info_plist_path.exists():
                    artifact.cls.process([info_plist_path],
                                         seeker, output_folder)
                else:
                    logger.info('Info.plist not found for iTunes Backup!')
                # GuiWindow.SetProgressBar(categories_searched * ratio)
        else:
            for regex in [*artifact.cls.search_dirs]:
                found = seeker.search(regex)

                if found:
                    artifact.cls.files_found.extend(found)
                    logger.info(f'Files for {regex} located at {found}')

                    logger.info(f'Artifact {artifact.cls.category}[{name}] processing...')
                    process_time = artifact.cls.get(seeker)
                    artifact.cls.process_time = process_time
                    logger.info(f'Artifact {artifact.cls.category}[{name}] finished in {artifact.cls.process_time}')

                    if artifact.cls.report():
                        logger.info(f'Report generated for {artifact.cls.category}[{name}]')


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

    def __get__(self, obj, type=None) -> List:
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
    """Descriptor ensuring 'files_found' type
    """
    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, type=None) -> Union[List, str]:
        value = obj.__dict__.get(self.name) or ''
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


class ReportHeaders:
    """Descriptor ensuring 'report_headers' type
    """
    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, type=None) -> Union[List, tuple]:
        return obj.__dict__.get(self.name) or ('Key', 'Value')

    def __set__(self, obj, value) -> None:
        if ReportHeaders._check_list_of_tuples(value, bool_list=[]):
            obj.__dict__[self.name] = value
        else:
            raise TypeError(
                'Error setting report headers! '
                'Expected list of tuples or tuple!'
            )

    @staticmethod
    def _check_list_of_tuples(values: List, bool_list: List[bool] = []) -> bool:
        """Checks list to see if its a list of tuples of strings

        Examples:

            Set headers for a single table
            self.report_headers = ('Timestamp', 'Account Desc.', 'Username',
                                   'Description', 'Identifier', 'Bundle ID')

            Set headers for more the one table
            self.report_headers = [('Timestamp', 'Account Desc.', 'Username',
                                    'Description', 'Identifier', 'Bundle ID'),
                                   ('Key', 'Value)]

            Anything else should fail to set.

        Args:
            values (list): values to be checked
            bool_list (list, optional): list of booleans of values checked.
                Defaults to [].

        Returns:
            bool: Returns true or false if values match for tuples of strings
        """
        if values == []:
            return all(bool_list)
        else:
            if isinstance(values, tuple):
                idx = values
                values = []
            elif isinstance(values, list):
                idx = values[:1][0]
                values = values[1:]
            else:
                return False

            if isinstance(idx, list):
                return ReportHeaders._check_list_of_tuples(values, bool_list)
            elif isinstance(idx, tuple):
                bool_list.extend([isinstance(it, str) for it in idx])
            else:
                bool_list.extend([False])
            return ReportHeaders._check_list_of_tuples(values, bool_list)


@dataclass
class _AbstractBase:
    name: str = field(init=False)


@dataclass
class _AbstractArtifactDefaults:
    category: str = field(init=False, default='None')
    description: str = field(init=False, default='')
    files_found: List[str] = field(init=False, repr=False, default=FilesFound())
    generate_report: bool = field(init=False, default=True)
    report_headers: Union[List, tuple] = field(
        init=False, default=ReportHeaders())
    search_dirs: List[str] = field(init=False, default=SearchDirs())
    web_icon: Icon = field(init=False, default=WebIcon())

    # These are used internally to track artifacts
    _core_artifact: bool = field(init=False, default=False)
    _long_running_process: bool = field(init=False, default=False)
    _selected_artifact: bool = field(init=False, default=False)


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
    def get(self, seeker: object) -> None:
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
    def data(self) -> List:
        """list: data found per artifact
        """
        return self._data

    @data.setter
    def data(self, data: List) -> List:
        self.html_report.data = data
        self._data = data

    @property
    def processing_time(self) -> str:
        return self._processing_time

    @processing_time.setter
    def processing_time(self, time: float) -> None:
        self._processing_time = time

    @property
    def selected(self) -> bool:
        return self._selected_artifact

    @property
    def core_artifact(self) -> bool:
        return self._core_artifact

    @property
    def long_running_process(self) -> bool:
        return self._long_running_process

    def report(self) -> bool:
        if self.generate_report is False:
            logger.error(f'Report not generated for {self.name}! Artifact '
                         f'marked for no report generation. Check artifact\'s '
                         f'\'generate_report\' attribute.')
            return False
        self.html_report.report(self.files_found)
        return True

    @classmethod
    def open_file(props: object, file: Union[str, Path], func: object) -> object:
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
    def close_file(props: object, file: Union[str, Path]) -> bool:
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


def core_artifact(cls):
    """Decorator to mark a core artifact
    """
    @functools.wraps(cls)
    def wrapper(cls):
        if issubclass(cls, AbstractArtifact):
            setattr(cls, '_core_artifact', True)
            setattr(cls, '_selected_artifact', True)
            return cls
        else:
            raise AttributeError(
                f'Class object {str(cls)} is an Artifact! '
                f'Error setting property \'core_artifact\' on class!'
            )
    return wrapper(cls)


def long_running_process(cls):
    """Decorator to mark a artifact as long running
    """
    @functools.wraps(cls)
    def wrapper(cls):
        if issubclass(cls, AbstractArtifact):
            setattr(cls, '_long_running_process', True)
            return cls
        else:
            raise AttributeError(
                f'Class object {str(cls)} is an Artifact! '
                f'Error setting property \'long_running_process\' on class!'
            )
    return wrapper(cls)


def select(name: str = None, all_artifacts=False, long_running_process=False, reset=True) -> None:
    """Toggles if an artifact should be run

       Core artifacts cannot be toggled. `all_artifacts` will not select any artifact
       marked as long running unless it also is set to True.

       If you want to ensure the state of the artifacts, call this with `reset=True` to
       reset all the states to their default values.

    Args:
        name (str, optional): short name of the artifact. Defaults to None.
        all_artifacts (bool, optional): bool to select all artifacts. Defaults to False.
        long_running_process (bool, optional): used with `all_artifacts` to select
            long running processes. Defaults to False.
        reset (bool, optional): clears the select flags on non-core artifacts. Defaults to True.
    """
    if reset:
        # resets all artifacts to be not selected
        for name in artifact_list:
            selected = artifact_list[name].cls.selected
            lrp = artifact_list[name].cls.long_running_process
            core = artifact_list[name].cls.core_artifact
            if not core:
                setattr(artifact_list[name].cls, '_selected_artifact', False)
    elif name is None and all_artifacts:
        for name in artifact_list:
            selected = artifact_list[name].cls.selected
            lrp = artifact_list[name].cls.long_running_process
            core = artifact_list[name].cls.core_artifact
            if lrp and not core:
                if long_running_process:
                    setattr(artifact_list[name].cls, '_selected_artifact', not selected)
            elif not core:
                setattr(artifact_list[name].cls, '_selected_artifact', not selected)
    elif not core:
        selected = artifact_list[name].cls.selected
        setattr(artifact_list[name].cls, '_selected_artifact', not selected)


artifact_list = _build_artifact_list()
