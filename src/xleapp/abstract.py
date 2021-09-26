import logging
import re
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from os import PathLike
from pathlib import Path
from typing import Union

import xleapp.globals as g
import xleapp.report.tsv as tsv
from xleapp.report.templating import HtmlPage, Template
from xleapp.report.webicons import Icon as Icon

logger = logging.getLogger(__name__)


class WebIcon:
    """Descriptor ensuring 'web_icon' type"""

    def __set_name__(self, owner, name):
        self.name = str(name)

    def __get__(self, obj, icon_type=Icon) -> object:
        return obj.__dict__.get(self.name) or Icon.ALERT_TRIANGLE

    def __set__(self, obj, value) -> None:
        if isinstance(value, Icon) or isinstance(value, WebIcon):
            obj.__dict__[self.name] = value
        else:
            raise TypeError(
                f"Got {type(value)} instead of {type(Icon)}! "
                f"Error setting Web Icon on {str(obj)}!",
            )


class ReportHeaders:
    """Descriptor ensuring 'report_headers' type"""

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, report_type=None) -> Union[list, tuple]:
        return obj.__dict__.get(self.name) or ("Key", "Value")

    def __set__(self, obj, value) -> None:
        if ReportHeaders._check_list_of_tuples(value, bool_list=[]):
            obj.__dict__[self.name] = value
        else:
            raise TypeError(
                "Error setting report headers! " "Expected list of tuples or tuple!",
            )

    @staticmethod
    def _check_list_of_tuples(values: list, bool_list: list[bool] = None) -> bool:
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
        bool_list = bool_list or []
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

    @Template("report_base")
    def html(self):
        return self.template.render(artifact=self.artifact, navigation=self.navigation)

    def report(self):
        html = self.html()
        output_file = (
            self.report_folder / f"{self.artifact.category} - {self.artifact.name}.html"
        )
        output_file.write_text(html)

        if self.artifact.processed:
            tsv.save(
                self.report_folder,
                self.artifact.report_headers,
                self.artifact.data,
                self.artifact.name,
            )

    def set_artifact(self, artifact):
        self.artifact_cls = type(artifact).__name__
        self.artifact = artifact


@dataclass
class _AbstractBase:
    """Base class to set any properties for
    `AbstractArtifact` Class. This properties do not
    have a default value.

    Attributes:
        name (str): full name of the artifact
        html_report (ArtifactHtmlReport): object holding options and
            information for the html for each artifact.
    """

    name: str = field(init=False)


@dataclass
class _AbstractArtifactDefaults:
    """Class to set defaults to any properties for the
    `AbstractArtifact` class.

    Attributes core, long_running_process, and selected are used
    to track artifacts internally for certain actions.

    Attributes:
        category (str): Category the artifact falls into. This also is used
            for the area the artifacts appears under for the end report.
            Default is None.
        core (bool): artifacts require to always run. Default is False.
        description (str): Short description of the artifact. Default is ''.
        found (list[str]): list of files located from the artifact's
            `process()` function
        generate_report (bool): bool to mark if the artifact should product
            a report. Some artifacts may product information used by other
            artifacts and such may not need a generated report. This
            suppresses the report.
        hide_html_report_path_table (bool): bool to hide displaying paths
            when then report is generated. Note: Any artifact processing 10
            or more files will ignore this value.
        long_running_process (bool): artifacts which takes an extremely
            long time to run and should be deselected by default.
            Default is False
        report_headers (list or tuple): headers for the report table during
            report generation.
        regex (list): search strings set by the `@Search()` decorator.
        processed (bool): True or False if the artifact was properly
            processed.
        selected: artifacts selected to be run. Default is False.
        web_icon (Icon): FeatherJS icon used for the report navgation menu
    """

    category: str = field(init=False, default="None")
    core: bool = field(init=False, default=False)
    data: list = field(init=False, default_factory=lambda: [])
    description: str = field(init=False, default="")
    found: list = field(init=False, default_factory=lambda: [])
    generate_report: bool = field(init=False, default=True)
    hide_html_report_path_table: bool = field(init=False, default=False)
    html_report: ArtifactHtmlReport = field(init=False, default=ArtifactHtmlReport())
    long_running_process: bool = field(init=False, default=False)
    report_headers: Union[list, tuple] = field(init=False, default=ReportHeaders())
    regex: list = field(init=False, default_factory=lambda: [])
    processed: bool = field(init=False, default=False)
    selected: bool = field(init=False, default=False)
    web_icon: Icon = field(init=False, default=WebIcon())


@dataclass
class AbstractArtifact(ABC, _AbstractArtifactDefaults, _AbstractBase):
    """Abstract class for creating Artifacts"""

    __slots__ = "__dict__"

    @abstractmethod
    def process(self) -> None:
        """Gets artifacts located in `files_found` params by the
        `seeker`. It saves should save the report in `report_folder`.
        """
        NotImplementedError(
            "Needs to implement AbastractArtifact's" "process() method!",
        )

    def pre_process(
        self,
        regex: list[str],
        file_names_only: bool = False,
        return_on_first_hit: bool = True,
    ) -> bool:
        seeker = g.seeker
        files = g.seeker.file_handles
        global_regex = files.keys()

        self.regex = regex
        wildcard_check = re.compile(r"(\b\w*[A-Za-z\/*.]+)$")

        for regex in self.regex:
            results = []

            if regex in global_regex:
                results = files[regex]
            else:
                try:
                    if return_on_first_hit:
                        results = [next(seeker.search(regex))]
                    else:
                        results = list(seeker.search(regex))
                except StopIteration:
                    results = None

                if bool(results):
                    files.add(regex, results, file_names_only)

            if bool(results):
                # Checks if a '*' (wildcard) is used to search.
                # Possible that one or more files can be returned.
                # You MUST return a list in this case back to the artifact class.
                # '-1' is no wildcard match and such should NOT return a list
                return_list = not (
                    wildcard_check.search(regex).group(1).find("*") == -1
                )

                if (return_on_first_hit or len(results) == 1) and not return_list:
                    self.found = files[regex].copy().pop()
                else:
                    self.found.extend(files[regex])
        return bool(self.found)

    @property
    def processed(self) -> bool:
        try:
            return len(self.found) > 0 and all(self.found)
        except TypeError:
            return bool(self.found)

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

    def report(self, report_folder: str) -> bool:
        """Generates report for artifact.

        Args:
            report_folder (str): Location of reports

        Returns:
            bool: True or False if the report was generated.
        """
        if self.generate_report is False:
            if self.core:
                logger.info(
                    "\t-> Report generation skipped for core artifacts!",
                    extra={"flow": "no_filter"},
                )
            else:
                logger.info(
                    f'\t-> Report not generated for "{self.name}"! Artifact '
                    "marked for no report generation. Check "
                    "artifact's 'generate_report' attribute.\n",
                    extra={"flow": "no_filter"},
                )
            return False

        self.html_report.report_folder = report_folder
        self.html_report.set_artifact(self)

        if self.processed:
            self.html_report.data = self.data
        self.html_report.report()

        return True

    def copyfile(self, input_file: Union[PathLike, str], output_file: str) -> None:
        """Exports file to report folder

        File will be located under report_folder\\export\\artifact_class

        Args:
            input_file (str): input file name/path
            output_file (str): output file name
        """
        report_folder = g.report_folder
        artifact_folder = type(self).__name__
        output_folder = Path(report_folder / "export" / artifact_folder)
        output_folder.mkdir(parents=True, exist_ok=True)

        shutil.copyfile(input_file, (output_folder / output_file))
        logger.debug(
            f"File {input_file.base} copied to " f"{output_folder / output_file}",
        )

    def rmfile(self, input_file: Union[PathLike, str]) -> None:
        """Removed file from report folder

        Args:
            input_file (Union[PathLike, str]): pathlike or str of file to
                remove. Must be located in the artifact's export folder.
        """
        artifact_name = type(self).__name__
        fp = Path(input_file)
        if artifact_name in fp.parts:
            try:
                fp.unlink()
            except OSError:
                logger.warning(
                    f'Attempting to delete "{fp}" failed! ' "File was not found!",
                )
        else:
            logger.warning(
                f'Artifact "{artifact_name}" attempted to '
                f"delete {fp} not located within its export folder.",
            )
