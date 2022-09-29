from __future__ import annotations

import datetime
import importlib
import logging
import typing as t

from collections import UserDict, defaultdict
from functools import cached_property
from importlib.metadata import entry_points
from pathlib import Path

import jinja2
import jinja2.ext
import PySimpleGUI as PySG
import xleapp.artifacts as artifacts
import xleapp.artifacts.services as artifact_service
import xleapp.plugins as plugins
import xleapp.report as report
import xleapp.report.db as db
import xleapp.templating as templating

from ._version import __project__, __version__
from .gui.utils import ProcessThread
from .helpers.descriptors import Validator
from .helpers.search import FileSeekerBase, search_providers
from .helpers.strings import split_camel_case
from .helpers.utils import is_list
from .templating.ext import IncludeLogFileExtension


__ARTIFACT_PLUGINS__ = artifact_service.Artifacts()

logger_log = logging.getLogger("xleapp.logfile")

if t.TYPE_CHECKING:
    BaseUserDict = UserDict[str, t.Any]
else:
    BaseUserDict = UserDict


class Device(BaseUserDict):
    """Device information for report"""

    def table(self) -> list[list[t.Any]]:
        """Creates list for table information on the "Device" Tab

        Returns:
            Returns the list of device information
        """
        data_list = []
        for key, value in self.data.items():
            key_camel_case = split_camel_case(key)
            data_list.append([" ".join(key_camel_case), value])
        return data_list


class OutputFolder(Validator):
    default_value: t.Any = None

    def validator(self, value: t.Union[str, Path]) -> None:
        if not isinstance(value, (str, Path)):
            raise TypeError(f"Expected {value!r} to be one of: str, Path!")
        if not Path(value).exists():
            raise FileNotFoundError(f"{value!r} must already exists!")


class Application:
    """Main application

    Attributes:
        debug (bool): debugging enabled. Default is False
        project (str): Name of the project
        version (str): Version of the project
        device (Device): Information about the device where the artifacts came from.
        default_configs (dict[str, t.Any]): Default configuration used for the
            application. Currently not used.
        extraction_type (str): Type of extraction being processed.
        report_folder (Path): Location of the report.
        log_folder (Path): Location of the log files. Resides in side the report folder.
        seeker (FileSeekerBase): Seeker to location find from the extraction.
        jinja_environment (jinja2.Environment): Jinja2 environment for processing and outputting
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
    jinja_environment = jinja2.Environment
    log_folder: Path
    output_path = OutputFolder()
    processing_time: float
    project: str
    report_folder: Path
    seeker: FileSeekerBase
    version: str
    dbservice: db.DBService

    def __init__(self, device_type: str) -> None:
        self.default_configs = {
            "thumbnail_root": "**/Media/PhotoData/Thumbnails/**",
            "media_root": "**/Media",
            "thumbnail_size": (256, 256),
        }

        self.device.update({"Type": device_type})
        self.discover_plugins()
        self.project = __project__
        self.version = __version__

    def __call__(
        self,
        *artifacts_list: str,
        output_path: t.Optional[Path] = None,
        input_path: Path,
    ) -> Application:
        self.output_path = output_path
        self.create_output_folder()
        self.input_path = input_path

        self.dbservice = db.DBService(self.report_folder)

        sorted_plugins = sorted(
            search_providers.data.items(),
            key=lambda kv: kv[1].priority,
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

        artifacts_str_list: t.Sequence[str]
        if artifacts_list:
            artifacts_str_list = [selected.lower() for selected in artifacts_list]

            for artifact in artifacts.AbstractBase.registry:
                if artifacts_list and type(artifact).__name__ in artifacts_str_list:
                    artifact.select = True  # type: ignore
                elif not artifacts_list:
                    artifact.select = True  # type: ignore
                else:
                    if not artifact.core:
                        artifact.select = False  # type: ignore
        return self

    @staticmethod
    def discover_plugins() -> t.Optional[dict[str, set[plugins.Plugin]]]:
        device_plugins: dict[str, set[plugins.Plugin]] = defaultdict(set)
        found = {
            plugin.name: importlib.import_module(plugin.module)
            for plugin in entry_points()["xleapp.plugins"]
        }

        if len(found) == 0:
            raise plugins.PluginMissingError("No plugins installed! Exiting!")

        for _, extension in found.items():
            for plugin in extension.__PLUGINS__:
                xleapp_plugin: plugins.Plugin = getattr(
                    plugin, f"{plugin.__name__.rpartition('.')[-1].capitalize()}Plugin"
                )
                device_plugins[plugin].add(xleapp_plugin())
        return device_plugins

    @cached_property
    def jinja_env(self) -> jinja2.Environment:
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

    def create_jinja_environment(self) -> jinja2.Environment:
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
        rv.filters.update(
            {
                "is_list": is_list,
            },
        )
        rv.globals.update(g=self)

        return rv

    @property
    def artifacts(self):
        return __ARTIFACT_PLUGINS__

    def run(
        self,
        window: t.Optional[PySG.Window],
        thread: t.Optional[ProcessThread],
    ) -> None:
        self.artifacts.run_queue(window=window, thread=thread)

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

        for artifact in artifacts.filter_artifacts(self.artifacts):
            msg_artifact = f"-> {artifact.category} [{artifact.cls_name}]"

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

            if artifact.processed and hasattr(artifact, "data"):
                artifact_name = artifact.value.name
                data_list = artifact.data
                data_headers = artifact.report_headers

                self.dbservice.save(
                    db_type="tsv",
                    name=artifact_name,
                    data_list=data_list,
                    data_headers=data_headers,
                )

                if artifact.kml:
                    self.dbservice.save(
                        db_type="kml",
                        name=artifact_name,
                        data_list=data_list,
                        data_headers=data_headers,
                    )

                if artifact.timeline:
                    self.dbservice.save(
                        db_type="timeline",
                        name=artifact_name,
                        data_list=data_list,
                        data_headers=data_headers,
                    )
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
