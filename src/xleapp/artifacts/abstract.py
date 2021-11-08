# -*- coding: utf-8 -*-
"""This module contains all the functions for Artifact abstract class.

Python requires that attributes with out default values come after attributes with defaults.

The class order ABC > AbstractArtifactDefaults > AbstractBase ensures this is correct.

:obj:`AbstractBase` contains all attributes without a default. Please place any extra attributes that do not require defaults within this class. Also ensure to use `field(init=false)` for each attribute so they are not required when the class is first created.

:obj:`AbstractArtifactDefaults` provides any attributes with defaults. Also, use `field(init=False)` for each one as before.

:obj:`Artifact` is the class every artifact needs to be subclassed from.

"""

from __future__ import annotations

import logging
import typing as t

from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

import xleapp.artifacts as artifacts

from .descriptors import FoundFiles, ReportHeaders, WebIcon


if t.TYPE_CHECKING:
    from xleapp.app import Application


@dataclass
class AbstractBase:
    """Base class to set any properties for :obj: `Artifact` Class."""

    description: str = field(init=False, repr=False, compare=False)
    name: str = field(init=False)
    data: list[t.Any] = field(init=False, repr=False, compare=False)
    regex: set[str] = field(init=False, repr=False, compare=False)
    app: Application = field(init=False, repr=False)
    _log: logging.Logger = field(init=False, repr=False, compare=False)


@dataclass
class AbstractArtifactDefaults:
    """Class to set defaults to any properties for the
    :obj:`Artifact` class.

    Attributes core, long_running_process, and selected are used
    to track artifacts internally for certain actions.
    """

    category: str = field(init=False, default="Unknown")
    core: bool = field(init=False, default=False)
    found: FoundFiles = field(init=False, default=FoundFiles())
    kml: bool = field(init=False, default=False)
    long_running_process: bool = field(init=False, default=False)
    processed: bool = field(init=False, default=False)
    process_time: float = field(init=False, default=float())
    report: bool = field(init=False, default=True)
    report_headers: ReportHeaders = field(init=False, default=ReportHeaders())
    select: bool = field(init=False, default=False)
    timeline: bool = field(init=False, default=False)
    web_icon: WebIcon = field(init=False, default=WebIcon())


@dataclass  # type: ignore  # https://github.com/python/mypy/issues/5374
class Artifact(ABC, AbstractArtifactDefaults, AbstractBase):
    """Abstract class for creating Artifacts"""

    @abstractmethod
    def process(self) -> None:
        """Gets artifacts located in `files_found` params by the
        `seeker`. It saves should save the report in `report_folder`.
        """
        raise NotImplementedError(
            "Needs to implement Artifact's" "process() method!",
        )

    @contextmanager
    def context(
        self,
        regex: set[str],
        file_names_only: bool = False,
        return_on_first_hit: bool = True,
    ) -> t.Iterator[Artifact]:
        """Creates a contaxt manager for an artifact.

        This will automatically search and add the regex and files to an artifact when
        called. You then can use `self.found` when processing the artifact.

        Example:
            This can be used with `with` blocks::

            >>> with Artifact.context({'*/myregex*'}, file_names_only=True) as artifact:
                    artifact.name = 'New Name'
                    artifact.process()

        Yields:
            Artifact: Updated object
        """
        seeker = self.app.seeker
        files = seeker.file_handles
        global_regex = files
        self.regex = regex
        for artifact_regex in self.regex:
            handles = None
            results = None
            if artifact_regex in global_regex:
                handles = files[artifact_regex]
            else:
                try:
                    if return_on_first_hit:
                        results = {next(seeker.search(artifact_regex))}
                    else:
                        results = set(seeker.search(artifact_regex))
                except StopIteration:
                    results = None

                if results:
                    files.add(artifact_regex, results, file_names_only)

            if handles or results:
                if return_on_first_hit or len(results) == 1:
                    self.found = self.found | {files[artifact_regex].copy().pop()}
                else:
                    self.found = self.found | files[artifact_regex]
        yield self

    def __enter__(self) -> Artifact:
        return self

    def __eq__(self, other) -> bool:
        return (self.name == other.name) and (self.category == self.category)

    @property
    def cls_name(self) -> str:
        """Returns class Name of object

        Returns:
            str: class name
        """
        return type(self).__name__

    @property
    def data_save_folder(self) -> Path:
        """Locate to save files from this artifact

        Returns:
            Path to the folder to save files
        """
        return Path(self.app.report_folder / "export" / self.cls_name)

    def copyfile(self, input_file: Path, output_file: str) -> Path:
        """Exports file to report folder

        File will be located under report_folder\\export\\artifact_class

        A shortcut for :func:`artifacts.copyfile()` inforcing the save
        location for each file.

        Args:
            input_file: input file name/path
            output_file: output file name

        Returns:
            output_file: Path object of the file save location and name.
        """
        return artifacts.copyfile(
            input_file=input_file,
            output_file=self.data_save_folder / output_file,
        )

    def log(self, level: int = logging.INFO, message: object = None) -> None:
        """Log message for this artifact

        Args:
            level: Logging message level. Defaults to logging.INFO.
            message: Message to log. Defaults to None.

        Raises:
            AttributeError: Error messae if :attr:`message` is not set.
        """
        if not hasattr(self, "_log"):
            self._log = logging.getLogger("xleapp.logfile")

        if not message:
            raise AttributeError(f"Message missing for log on {self.cls_name}!")

        self._log.log(level, msg=message)
