import importlib
import inspect
import io
import logging
import os
import traceback
from abc import ABC, abstractmethod
from collections import OrderedDict, defaultdict, namedtuple
from pathlib import Path
from textwrap import TextWrapper

import ileapp.html_report.artifact_report as html_report
import prettytable
from ileapp.globals import props
from ileapp.helpers import is_platform_windows
from ileapp.helpers.decorators import timer
from ileapp.helpers.search_files import (FileSeekerDir, FileSeekerItunes,
                                         FileSeekerTar, FileSeekerZip)
from ileapp.html_report import Icon

logger = logging.getLogger(__name__)

# Setup named tuple to hold each artifact
Artifact = namedtuple('Artifact', ['name', 'cls'])
Artifact.__doc__ += ': Loaded forensic artifact'
Artifact.cls.__doc__ = 'Artifact object class'
Artifact.name.__doc__ = 'Artifact short name'


class AbstractArtifact(ABC):
    """Abstract class for creating Artifacts
    """

    _name = 'Unknown Artifact'
    _core_artifact = False
    _long_running_process = False
    _web_icon = Icon.ALERT_TRIANGLE
    _category = 'None'
    _report_headers = ('Key', 'Values')
    _files_found = []
    _description = ''
    _generate_report = True
    _props = None

    def __init__(self, props):
        self.html_report = html_report.ArtifactHtmlReport(self)
        self._props = props

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
    def props(self):
        return self._props

    @property
    def long_running_process(self):
        """True if this artifact takes an extremely long time to run.

            Set to true to mark this artifact has having an extremely
            long run time during processing of the artifact. Artifacts
            whose run time is greater then 2 mins probably need to
            have this value set.

            This will cause the artifact not to be select by default
            when using the GUI;

            Returns:
                bool: True/False if long running process
        """
        return self._long_running_process

    @property
    def web_icon(self):
        """
        str: Returns Bootstrap web icon class for this artifact
        """
        return self._web_icon

    @property
    def name(self):
        """
        str: Long name of the Artifact
        """
        return self._name

    @property
    def search_dirs(self):
        """
        tuple: Tuple containing search regex for
        location of files containing the Artifact.
        """
        if isinstance(self._search_dirs, str):
            return [self._search_dirs]
        if isinstance(self._search_dirs, tuple):
            return [*self._search_dirs]
        return self._search_dirs

    @property
    def category(self):
        """
        str: Section of the report the artifacts shows under.
        """
        return self._category

    @property
    def core_artifact(self):
        """bool: Sets if this is a core artifact
        """
        return self._core_artifact

    @property
    def report_folder(self):
        """Wrapper for the report folder object
        """

        return self.props.run_time_info['report_folder']

    @property
    def files_found(self):
        """list: files or folders found for an artifact
        """
        if (isinstance(self._files_found, list)
                and len(self._files_found) == 1):
            return self._files_found[0]
        return self._files_found

    @files_found.setter
    def files_found(self, files):
        self._files_found = files

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
    def report_headers(self):
        return self._report_headers

    @property
    def process_time(self):
        """Processing time of the artifact
        """
        self._process_time

    @process_time.setter
    def process_time(self, time):
        self._process_time = time

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, description):
        self._description = description

    @property
    def generate_report(self):
        return self._generate_report

    @generate_report.setter
    def generate_report(self, bool):
        self._generate_report = bool

    def report(self):
        if self.generate_report is False:
            logger.error(f'Report not generated for {self.name}! Artifact marked for no '
                         f'report generation. Check artifact\'s \'generate_report\' attribute.')
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


def get_list_of_artifacts(props, ordered=True):
    """Generates a List of Artifacts installed

    Args
        ordered(bool): sets if the true order of the artifacts
            is return; otherwise returns certain artifacts
            at the beginning of the dict

    Returns:
        OrderedDict or dict: dictionary of artifacts with short names as keys
    """
    logger.debug('Generating artifact lists from file system...')
    module_dir = Path(importlib.util.find_spec(__name__).origin).parent
    artifact_list = OrderedDict() if ordered else {}

    for it in module_dir.glob('*.py'):
        if (it.suffix == '.py' and it.stem not in ['__init__']):

            module_name = f'{__name__}.{it.stem}'
            module = importlib.import_module(module_name)
            module_members = inspect.getmembers(module, inspect.isclass)
            for name, cls in module_members:
                if (not str(cls.__module__).endswith('Artifact')
                        and str(cls.__module__).startswith(__name__)
                        and not inspect.isabstract(cls)):

                    tmp_artifact_obj = cls(props)
                    tmp_artifact = Artifact(
                        name=tmp_artifact_obj.name,
                        cls=tmp_artifact_obj
                    )
                    artifact_list.update({name: tmp_artifact})

    # sort the artifact list
    tmp_artifact_list = sorted(list(artifact_list.items()))
    artifact_list.clear()
    artifact_list.update(tmp_artifact_list)

    logger.debug(f'Artifacts loaded: { len(artifact_list) }')
    return artifact_list


def generate_artifact_path_list():
    """Generates path file for usage with Autopsy
    """
    logger.info('Artifact path list generation started.')

    with open('path_list.txt', 'w') as paths:
        regex_list = []
        for key, value in get_list_of_artifacts(ordered=True).items():
            # Creates instance of each artifact class
            artifact = value['class']
            if isinstance(artifact.search_dirs, tuple):
                [regex_list.append(item) for item in artifact.search_dirs]
            else:
                regex_list.append(artifact.search_dirs)
        # Create a single list removing duplications
        ordered_regex_list = '\n'.join(set(regex_list))
        logger.info(ordered_regex_list)
        paths.write(ordered_regex_list)

        logger.info('Artifact path list generation completed')


def generate_artifact_table():
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
        for key, val in props.installed_artifacts.items():
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


@timer
def crunch_artifacts(search_list, extracttype, input_path, output_folder):
    seeker = None

    if extracttype == 'fs':
        seeker = FileSeekerDir(input_path)

    elif extracttype in ('tar', 'gz'):
        seeker = FileSeekerTar(input_path, props.run_time_info['temp_folder'])

    elif extracttype == 'zip':
        seeker = FileSeekerZip(input_path, props.run_time_info['temp_folder'])

    elif extracttype == 'itunes':
        seeker = FileSeekerItunes(input_path, props.run_time_info['temp_folder'])

    logger.debug(f'Extract type is {extracttype} ')
    # Parse core artifacts first
    crunch_core_artifacts(extracttype, seeker, input_path, output_folder)

    search_regexes = build_search_regex_list(search_list)

    for regex, artifacts in search_regexes.items():
        found = seeker.search(regex)

        if found:
            logger.info(f'Files for {regex} located at {found}')

        for name in artifacts:
            artifact = props.installed_artifacts[name]

            if artifact.cls.core_artifact:
                break

            artifact.cls.files_found = found
            logger.info(f'Artifact {artifact.cls.category}[{name}] processing...')
            process_time = artifact.cls.get(seeker)
            artifact.cls.process_time = process_time
            logger.info(f'Artifact {artifact.cls.category}[{name}] finished in {artifact.cls.process_time}')

            artifact.cls.report()
    return True


def build_search_regex_list(search_list):
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
