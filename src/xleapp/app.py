import datetime
import logging
import os
import typing as t

from collections import UserDict
from enum import Enum
from functools import cached_property
from pathlib import Path

import jinja2

from jinja2 import Environment

import xleapp.artifacts as artifacts
import xleapp.templating as templating

from xleapp.helpers.descriptors import Validator

from ._version import __project__, __version__
from .artifacts.services import ArtifactError, Artifacts
from .helpers.search import FileSeekerBase
from .templating._ext import IncludeLogFileExtension


logger_log = logging.getLogger("xleapp.logfile")


class Device(UserDict):
    def table(self):
        return [[key, value] for key, value in self.data.items()]


class OutputFolder(Validator):
    def validator(self, value):
        if not isinstance(value, (str, Path, os.PathLike)):
            raise TypeError(f"Expected {value!r} to be one of: str, Path, or Pathlike!")
        if not Path(value).exists():
            raise FileNotFoundError(f"{value!r} must already exists!")


class XLEAPP:
    """Main application

    Attributes:
        debug (bool): debugging enabled. Default is False
        project (str): Name of the project
        version (str): Version of the project
        device (Device): Information about the device where the artifacts came from.
        default_configs (dict[str, t.Any]): Default configuration used for the
            application. Currently not used.
        extraction_type (str): Type of extraction being processed.
        report_folder (Path): Location of the repot.
        log_folder (Path): Location of the log files. Resides in side the report folder.
        seeker (FileSeekerBase): Seeker to location find from the extraction.
        jinja_environment (Enviroment): Jinja2 environment for processing and outputing
            HTML reports.
        processing_type (float): Total about of time to run application after initial
            setup.
        input_path (Path): File or Folder of the extraction.
        output_path (Path): Parent folder of the report where the report folder is
            created.

    Raises:
        ArtifactError: Error if an artifacts fails for some reason
    """

    debug: bool = False
    project: str
    version: str
    device: Device = Device()
    default_configs: dict[str, t.Any] = {}
    extraction_type: str
    report_folder: Path
    log_folder: Path
    seeker: FileSeekerBase
    jinja_environment = Environment
    processing_time: float
    input_path: Path
    output_folder = OutputFolder()

    def __init__(
        self,
        *artifacts,
        output_folder: Path,
        input_path: Path,
        device_type: str,
        extraction_type: str,
    ) -> None:
        self.default_configs = {
            "thumbnail_root": "**/Media/PhotoData/Thumbnails/**",
            "media_root": "**/Media",
            "thumbnail_size": (256, 256),
        }

        self.project = __project__
        self.version = __version__
        self.output_folder = output_folder
        self.create_output_folder()
        self.input_path = input_path
        self.extraction_type = extraction_type
        self.device["type"] = device_type

        # If an Itunes backup, use that artifact otherwise use
        # 'LastBuild' for everything else.
        if self.extraction_type == "itunes":
            self.artifacts.LAST_BUILD.select = False
        else:
            self.artifacts.ITUNES_BACKUP_INFO.select = False

        choosen_artifacts = [name.lower() for name in artifacts]
        if not choosen_artifacts:
            # If no artifacts selected then choose all of them.
            self.artifacts.select(all=True)
        else:
            filtered_artifacts = filter(
                lambda artifact: (
                    artifact.cls_name.lower() in choosen_artifacts and not artifact.core
                ),
                self.artifacts,
            )

            # Remove the 'core' group of artifacts from this list.
            # It is not a "true" artifact.
            if 'core' in choosen_artifacts:
                choosen_artifacts.remove('core')

            for artifact in filtered_artifacts:
                try:
                    choosen_artifacts.remove(artifact.cls_name.lower())
                except ValueError:
                    # Core artifacts are not usually not given on the CLI. However,
                    # if they are specified, they are removed from this list.
                    pass

                artifact.select = True

            if len(choosen_artifacts) > 0:
                raise ArtifactError(f"Artifact(s) - {choosen_artifacts!r} not valid!")

    @cached_property
    def jinja_env(self) -> Environment:
        return self.create_jinja_environment()

    def create_output_folder(self):
        now = datetime.datetime.now()
        current_time = now.strftime("%Y-%m-%d_%A_%H%M%S")

        rf = self.report_folder = (
            Path(self.output_folder) / f"xLEAPP_Reports_{current_time}"
        )

        tf = self.temp_folder = rf / "temp"
        lf = self.log_folder = rf / "Script Logs"
        lf.mkdir(parents=True, exist_ok=True)
        tf.mkdir(parents=True, exist_ok=True)

    def create_jinja_environment(self) -> Environment:
        template_loader = jinja2.PackageLoader("xleapp.templating", "templates")
        log_file_loader = jinja2.FileSystemLoader(self.log_folder)

        options = {
            "loader": jinja2.ChoiceLoader([template_loader, log_file_loader]),
            "autoescape": jinja2.select_autoescape(["html", "xml"]),
            "extensions": [jinja2.ext.do, IncludeLogFileExtension],
            "trim_blocks": True,
            "lstrip_blocks": True,
        }
        rv = self.jinja_environment(**options)
        rv.globals.update(g=self)

        return rv

    @cached_property
    def artifacts(self) -> Enum:
        return Artifacts(self)

    def crunch_artifacts(self) -> None:
        return artifacts.crunch_artifacts(self)

    def generate_artifact_table(self):
        return artifacts.generate_artifact_table(self.artifacts)

    def generate_artifact_path_list(self):
        return artifacts.generate_artifact_path_list(self.artifacts)

    def generate_reports(self):
        logger_log.info("\nGenerating artifact report files...")
        nav = templating.generate_nav(
            report_folder=self.report_folder,
            artifacts=self.artifacts,
        )
        for artifact in artifacts.filter_artifacts(self.artifacts):
            msg_artifact = f"-> {artifact.category} [{artifact.cls_name}]"
            if not artifact.core:
                if artifact.report:
                    html_report = templating.ArtifactHtmlReport(
                        report_folder=self.report_folder,
                        log_folder=self.log_folder,
                        extraction_type=self.extraction_type,
                        navigation=nav,
                    )
                    if html_report(artifact).report:
                        logger_log.info(f"{msg_artifact}")
                else:
                    logger_log.warn(
                        f"{msg_artifact}: "
                        "Report not generated! Artifact "
                        "marked for no report generation. Check "
                        "artifact's 'report' attribute.",
                    )
            else:
                logger_log.info(f"{msg_artifact}: Report skipped for core artifacts!")
        logger_log.info("Report files generated!")
        logger_log.info(f"Report location: {self.output_folder}")

    @property
    def num_to_process(self):
        return len(
            {artifact.cls_name for artifact in self.artifacts if artifact.select},
        )

    @property
    def num_of_categories(self):
        return len(
            {artifact.value.category for artifact in self.artifacts if artifact.select},
        )
