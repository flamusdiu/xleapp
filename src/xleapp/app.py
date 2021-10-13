import datetime
from enum import Enum
import importlib
import inspect
import logging
import typing as t
from collections import UserDict
from functools import cached_property
from importlib.metadata import entry_points
from pathlib import Path

import jinja2
from jinja2 import Environment

import xleapp.artifacts as artifacts
import xleapp.templating as templating

from ._version import __project__, __version__
from .artifacts.services import generate_artifact_enum
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

    default_configs: dict[str, t.Any] = dict()

    extraction_type: str

    report_folder: Path

    log_folder: Path

    seeker: FileSeekerBase

    jinja_environment = Environment

    processing_time: float

    input_path: Path

    output_folder = OutputFolder()

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
    def artifacts(self) -> Enum:
        return generate_artifact_enum(self)

    def crunch_artifacts(self) -> None:
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
                for artifact in self.artifacts
                if artifact.value.selected
            }
        )

    @property
    def num_of_categories(self):
        return len(
            {
                artifact.value.category
                for artifact in self.artifacts
                if artifact.value.selected
            }
        )