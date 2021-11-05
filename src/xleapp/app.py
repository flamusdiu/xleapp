from __future__ import annotations

import datetime
import logging
import typing as t

from collections import UserDict
from functools import cached_property
from pathlib import Path

import jinja2
import PySimpleGUI as PySG

from jinja2 import Environment

import xleapp.artifacts as artifacts
import xleapp.report as report
import xleapp.templating as templating

from xleapp.plugins import Plugin

from ._version import __project__, __version__
from .gui.utils import ProcessThread
from .helpers.descriptors import Validator
from .helpers.search import FileSeekerBase, search_providers
from .helpers.utils import discovered_plugins
from .templating.ext import IncludeLogFileExtension


logger_log = logging.getLogger("xleapp.logfile")

if t.TYPE_CHECKING:
    from .artifacts import Artifacts
    from .artifacts.services import ArtifactEnum

    BaseUserDict = UserDict[str, t.Any]
else:
    BaseUserDict = UserDict


class Device(BaseUserDict):
    def table(self) -> list[list[t.Any]]:
        return [[key, value] for key, value in self.data.items()]


class OutputFolder(Validator):
    def validator(self, value: t.Union[str, Path]) -> None:
        if not isinstance(value, (str, Path)):
            raise TypeError(f"Expected {value!r} to be one of: str, Path!")
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
    default_configs: dict[str, t.Any]
    device: Device = Device()
    extraction_type: str
    input_path: Path
    jinja_environment = Environment
    log_folder: Path
    output_path = OutputFolder()
    processing_time: float
    project: str
    plugins: t.Optional[dict[str, set[Plugin]]]
    report_folder: Path
    seeker: FileSeekerBase
    version: str

    def __init__(self) -> None:
        self.default_configs = {
            "thumbnail_root": "**/Media/PhotoData/Thumbnails/**",
            "media_root": "**/Media",
            "thumbnail_size": (256, 256),
        }

        self.project = __project__
        self.version = __version__

        self.plugins = discovered_plugins()

    def __call__(
        self,
        *artifacts_list: str,
        device_type: t.Optional[str] = None,
        output_path: t.Optional[Path] = None,
        input_path: Path,
    ) -> XLEAPP:
        self.output_path = output_path
        self.create_output_folder()
        self.input_path = input_path
        self.device.update({"type": device_type})

        sorted_plugins = sorted(
            search_providers.data.items(),
            key=lambda kv: kv[1].priorty,
        )
        for extraction_type, _ in sorted_plugins:
            provider: FileSeekerBase = search_providers(
                extraction_type=extraction_type.upper(),
                input_path=input_path,
                temp_folder=self.temp_folder,
            )
            if provider.validate:
                self.seeker = provider
                self.extraction_type = extraction_type
                break

        artifacts_enum = self.artifacts.data
        artifact: ArtifactEnum
        artifacts_str_list: t.Sequence[str]
        if artifacts_list:
            artifacts_str_list = [selected.lower() for selected in artifacts_list]
        for artifact in artifacts_enum:
            if artifacts_list and artifact.cls_name.lower() in artifacts_str_list:
                artifacts_enum[artifact.name].select = True  # type: ignore
            elif not artifacts_list:
                artifacts_enum[artifact.name].select = True  # type: ignore
            else:
                artifacts_enum[artifact.name].select = False  # type: ignore

        return self

    @cached_property
    def jinja_env(self) -> Environment:
        return self.create_jinja_environment()

    def create_output_folder(self) -> None:
        now = datetime.datetime.now()
        current_time = now.strftime("%Y-%m-%d_%A_%H%M%S")

        rf = self.report_folder = (
            Path(self.output_path) / f"xLEAPP_Reports_{current_time}"
        )

        tf = self.temp_folder = rf / "temp"
        lf = self.log_folder = rf / "Script Logs"
        lf.mkdir(parents=True, exist_ok=True)
        tf.mkdir(parents=True, exist_ok=True)

    def create_jinja_environment(self) -> Environment:
        template_loader = jinja2.PackageLoader("xleapp.templating", "templates")
        log_file_loader = jinja2.FileSystemLoader(self.log_folder)

        options: dict[str, t.Any] = {
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
    def artifacts(self) -> Artifacts:
        return artifacts.Artifacts(self)

    def crunch_artifacts(
        self,
        window: t.Optional[PySG.Window],
        thread: t.Optional[ProcessThread],
    ) -> None:
        self.artifacts.crunch_artifacts(window=window, thread=thread)

    def generate_artifact_table(self) -> None:
        artifacts.generate_artifact_table(self.artifacts)

    def generate_artifact_path_list(self) -> None:
        artifacts.generate_artifact_path_list(self.artifacts)

    def generate_reports(self) -> None:
        logger_log.info("\nGenerating artifact report files...")
        report.copy_static_files(self.report_folder)
        nav = templating.generate_nav(
            report_folder=self.report_folder,
            artifacts=self.artifacts,
        )
        artifact: ArtifactEnum
        for artifact in artifacts.filter_artifacts(self.artifacts.data):
            msg_artifact = f"-> {artifact.category} [{artifact.cls_name}]"
            if not artifact.core:
                if artifact.report and artifact.select:
                    html_report = templating.ArtifactHtmlReport(
                        report_folder=self.report_folder,
                        log_folder=self.log_folder,
                        extraction_type=self.extraction_type,
                        navigation=nav,
                    )

                    if html_report(artifact).report:  # type: ignore
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
        logger_log.info(f"Report location: {self.output_path}")

    @property
    def num_to_process(self) -> int:
        return len(
            {artifact.cls_name for artifact in self.artifacts.data if artifact.select},
        )

    @property
    def num_of_categories(self) -> int:
        return len(
            {artifact.category for artifact in self.artifacts.data if artifact.select},
        )
