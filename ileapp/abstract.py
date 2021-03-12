import logging
from os import PathLike
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from io import FileIO
from typing import List, Union

import ileapp.report.tsv as tsv
from ileapp.report.templating import HtmlPage, Template
from ileapp.report.webicons import Icon as Icon

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


class FilesFound:
    """Descriptor ensuring 'found' type
    """
    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, type=None) -> Union[List, str]:
        if (obj.__dict__.get(self.name) is not None
                and len(obj.__dict__.get(self.name)) == 1):
            return obj.__dict__.get(self.name)[0]
        return obj.__dict__.get(self.name) or []

    def __set__(self, obj, value) -> None:
        if (isinstance(value, tuple)
                or isinstance(value, sqlite3.Connection)
                or isinstance(value, FileIO)):
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
class ArtifactHtmlReport(HtmlPage):

    artifact: object = field(init=False, default=None)
    data: list = field(init=False, default_factory=lambda: [])
    report_folder: PathLike = field(init=False, default=None)

    @Template('report_base')
    def html(self):
        return self.template.render(artifact=self.artifact)

    def report(self, found):
        html = self.html(found)
        output_file = (
            self.report_folder
            / f'{self.artifact.category} - {self.artifact.name}.html'
        )
        output_file.write_text(html)

        if self.artifact.processed:
            tsv.save(
                self.report_folder,
                self.artifact.report_headers,
                self.artifact.data,
                self.artifact.name)

    def set_artifact(self, artifact):
        self.artifact_cls = type(artifact).__name__
        self.artifact = artifact


@dataclass
class _AbstractBase:
    """ Base class to set any properties for
        `AbstractArtifact` Class. This properties do not
        have a default value.

        Properties:
            name (str): full name of the artifact
            html_report (ArtifactHtmlReport): object holding options and
                information for the html for each artifact.
    """
    name: str = field(init=False)


@dataclass
class _AbstractArtifactDefaults:
    """ Class to set defaults to any properies for the
        `AbstractArtifact` class.

        Properties:
            category (str): Category the artifact falls into. This also is used
                for the area the artifacts appears under for the end report.
                Default is None.
            description (str): Short description of the artifact. Default is ''.
            found (list[str]): list of files located from the artifact's
                `process()` function
            generate_report (bool): bool to mark if the artifact should product
                a report. Some artifacts may product information used by other
                artifacts and such may not need a generated report. This
                supresses the report.
            report_headers (list or tuple): headers for the report table during
                report generation.
            regex (list): search strings set by the `@Search()` decorator.
            processed (bool): True or False if the artiface was properly
                processed.
            web_icon (Icon): FeatherJS icon used for the report navgation menu
    """

    category: str = field(init=False, default='None')
    data: List = field(init=False, default_factory=lambda: [])
    description: str = field(init=False, default='')
    found: List = field(init=False, default=FilesFound())
    generate_report: bool = field(init=False, default=True)
    html_report: ArtifactHtmlReport = (
        field(init=False, default=ArtifactHtmlReport()))
    report_headers: Union[List, tuple] = field(
        init=False, default=ReportHeaders())
    regex: list = field(init=False, default_factory=lambda: [])
    processed: bool = field(init=False, default=False)
    web_icon: Icon = field(init=False, default=WebIcon())

    """
        These are used internally to track artifacts

        Properties:
            core (bool): artifacts require to always run. Default is False.
            long_running_process (bool): artifacts which takes an extemely
                long time to run and should be deselected by default.
                Default is False
            selected: artifacts selected to be run. Default is False.
    """
    core: bool = field(init=False, default=False)
    long_running_process: bool = field(init=False, default=False)
    selected: bool = field(init=False, default=False)


@dataclass
class AbstractArtifact(ABC, _AbstractArtifactDefaults, _AbstractBase):
    """Abstract class for creating Artifacts
    """
    __slots__ = '__dict__'

    @abstractmethod
    def process(self) -> None:
        """Gets artifacts located in `files_found` params by the
        `seeker`. It saves should save the report in `report_folder`.
        """
        NotImplementedError("Needs to implement AbastractArtifact's"
                            "process() method!")

    @property
    def processed(self) -> bool:
        return len(self.found) > 0 and all(self.found)

    @property
    def processing_time(self) -> str:
        """Processing time of the artifact

        Returns:
            str: str representation of the processing time
        """
        return self._processing_time

    @processing_time.setter
    def processing_time(self, time: float) -> None:
        self._processing_time = time

    def report(self, report_folder) -> bool:
        """ Generates report for artifact.

        Returns:
            bool: True or False if the report was generated.
        """
        if self.generate_report is False:
            if self.core:
                logger.info('Report generation skipped for core artifacts!', 
                            extra={'flow': 'no_filter'})
            else:
                logger.info(f'Report not generated for "{self.name}"! Artifact '
                            'marked for no report generation. Check '
                            'artifact\'s \'generate_report\' attribute.\n',
                            extra={'flow': 'no_filter'})
            return False

        self.html_report.report_folder = report_folder
        self.html_report.set_artifact(self)

        if self.processed:
            self.html_report.data = self.data
        self.html_report.report(self.found)

        return True
