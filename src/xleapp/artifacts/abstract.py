import logging
import shutil
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from io import FileIO
from os import PathLike
from pathlib import Path
from re import escape
from sqlite3.dbapi2 import Time
from typing import Iterator, Union

import xleapp.globals as g
from xleapp.artifacts.descriptors import FoundFiles, ReportHeaders, WebIcon
from xleapp.artifacts.html import ArtifactHtmlReport
from xleapp.log import init
from xleapp.report.webicons import Icon as Icon

logger = logging.getLogger(__name__)


@dataclass
class _AbstractBase:
    """Base class to set any properties for
    `AbstractArtifact` Class. This properties do not
    have a default value.

    Attributes:
        name (str): full name of the artifact
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
            processed. Default is False.
        processing_time(float): Seconds of time it takes to process this artifact.
            Default is 0.0.
        selected: artifacts selected to be run. Default is False.
        web_icon (Icon): FeatherJS icon used for the report navgation menu
        kml (bool): True or False to generate kml (location files) information
        timeline(bool): True or False to add data to the timeline database
    """

    category: str = field(init=False, default="None")
    core: bool = field(init=False, default=False)
    data: list = field(init=False, default_factory=lambda: [])
    description: str = field(init=False, default="")
    generate_report: bool = field(init=False, default=True)
    hide_html_report_path_table: bool = field(init=False, default=False)
    html_report: ArtifactHtmlReport = field(init=False, default=ArtifactHtmlReport())
    long_running_process: bool = field(init=False, default=False)
    report_headers: Union[list, tuple] = field(init=False, default=ReportHeaders())
    regex: list = field(init=False, default_factory=lambda: [])
    processed: bool = field(init=False, default=False)
    processing_time: float = field(init=False, default=0.0)
    selected: bool = field(init=False, default=False)
    web_icon: Icon = field(init=False, default=WebIcon())
    kml: bool = field(init=False, default=False)
    timeline: bool = field(init=False, default=False)
    found: set = field(init=False, default=FoundFiles())


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

        for regex in self.regex:
            results = []

            if regex in global_regex:
                results = files[regex]
            else:
                try:
                    if return_on_first_hit:
                        results = {next(seeker.search(regex))}
                    else:
                        results = set(seeker.search(regex))
                except StopIteration:
                    results = None

                if bool(results):
                    files.add(regex, results, file_names_only)

            if bool(results):
                if return_on_first_hit or len(results) == 1:
                    self.found = {files[regex].copy().pop()}
                else:
                    self.found = self.found | files[regex]
        return bool(getattr(self, "found", False))

    @property
    def processed(self) -> bool:
        try:
            return len(self.found) > 0 and all(self.found)
        except TypeError:
            return bool(self.found)
        except AttributeError:
            return False

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
