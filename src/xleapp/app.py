import datetime
import importlib
import inspect
import logging
from collections import UserDict
from functools import cached_property
from importlib.metadata import entry_points
from pathlib import Path

import jinja2
from jinja2 import Environment

import xleapp.artifacts as artifacts
import xleapp.templating as templating

from ._version import __project__, __version__
from .artifacts.services import ArtifactService, ArtifactServiceBuilder
from .helpers.search import FileSeekerBase
from .templating._ext import IncludeLogFileExtension

logger_log = logging.getLogger("xleapp.logfile")


class Device(UserDict):
    def table(self):
        return [[key, value] for key, value in self.data.items()]


class OutputFolder:
    def __set_name__(self, owner, name):
        self.name = str(name)

    def __get__(self, obj, type=None):
        return obj.__dict__.get(self.name) or None

    def __set__(self, obj, value):
        now = datetime.datetime.now()
        current_time = now.strftime("%Y-%m-%d_%A_%H%M%S")

        obj.__dict__[self.name] = value
        rf = obj.__dict__["report_folder"] = (
            Path(value) / f"xLEAPP_Reports_{current_time}"
        )

        tf = obj.__dict__["temp_folder"] = rf / "temp"
        lf = obj.__dict__["log_folder"] = rf / "Script Logs"
        lf.mkdir(parents=True, exist_ok=True)
        tf.mkdir(parents=True, exist_ok=True)


class XLEAPP:

    debug: bool = False

    project: str

    version: str

    device: Device = Device()

    default_configs = dict()

    extraction_type: str

    report_folder: Path

    log_folder: Path

    seeker: FileSeekerBase

    jinja_environment = Environment

    processing_time: float

    input_path: Path

    output_folder: Path = OutputFolder()

    def __init__(self, output_folder: Path, input_path: Path, device_type: str) -> None:
        self.default_configs = {
            "thumbnail_root": "**/Media/PhotoData/Thumbnails/**",
            "media_root": "**/Media",
            "thumbnail_size": (256, 256),
        }

        self.project = __project__
        self.version = __version__
        self.output_folder = output_folder
        self.input_path = input_path
        self.device["type"] = device_type

    @cached_property
    def jinja_env(self) -> Environment:
        return self.create_jinja_environment()

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
    def artifacts(self) -> dict:
        return self.create_artifact_list()

    def create_artifact_list(self) -> ArtifactService:
        """Generates a List of Artifacts installed

        Returns:
            Artifacts: dictionary of artifacts with short names as keys
        """

        logger_log.debug("Generating artifact lists from file system...")

        discovered_plugins = [
            plugin
            for plugin in entry_points()["xleapp.plugins"]
            if plugin.name == self.device.get("type")
        ]

        core_services = ArtifactService()
        services = ArtifactService()

        for plugin in discovered_plugins:
            # Plugins return a str which is the plugin direction to
            # find plugins inside of. This direction is loading
            # that directory. Then, all the plugins are loaded.
            module_dir = Path(plugin.load()())

            for it in module_dir.glob("*.py"):
                if it.suffix == ".py" and it.stem not in ["__init__"]:
                    module_name = f'{".".join(module_dir.parts[-2:])}.{it.stem}'
                    module = importlib.import_module(module_name, inspect.isfunction)
                    module_members = inspect.getmembers(module, inspect.isclass)
                    for name, cls in module_members:
                        # check MRO (Method Resolution Order) for
                        # Artifact classes. Also, insure
                        # we do not get an abstract class.
                        if (
                            len(
                                {str(name).find("Artifact") for name in cls.mro()}
                                - {-1},
                            )
                            != 0
                            and not inspect.isabstract(cls)
                        ):
                            builder = ArtifactServiceBuilder()
                            cls.app = self
                            artifact = builder(cls)
                            if cls.core:
                                core_services.register_builder(name.lower(), artifact)
                            else:
                                services.register_builder(name.lower(), artifact)

        # Creates dict with core artifacts up front
        # per Python 3.7 docs, this will keep them ordered.
        core_services.data.update(services.data)
        logger_log.debug(f"Artifacts loaded: {len(core_services)}")

        return core_services

    def crunch_artifacts(self):
        return artifacts.crunch_artifacts(self)

    def generate_artifact_table(self):
        return artifacts.generate_artifact_table(self.artifacts)

    def generate_artifact_path_list(self):
        return artifacts.generate_artifact_path_list(self.artifacts)

    def generate_reports(self):
        logger_log.info("\nGenerating artifact report files...")
        nav = templating.generate_nav(
            report_folder=self.report_folder, artifacts=self.artifacts
        )
        for artifact in artifacts.filter_artifacts(self.artifacts.values()):
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
                        "artifact's 'report' attribute."
                    )
            else:
                logger_log.info(f"{msg_artifact}: Report skipped for core artifacts!")
        logger_log.info("Report files generated!")

    @property
    def num_to_process(self):
        return len(
            {
                artifact.cls_name
                for artifact in self.artifacts.values()
                if artifact.selected
            }
        )

    @property
    def num_of_categories(self):
        return len(
            {
                artifact.category
                for artifact in self.artifacts.values()
                if artifact.selected
            }
        )
