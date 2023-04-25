"""This module contains all the functions for Artifact abstract class.

Python requires that attributes with out default values come after attributes with defaults.

The class order ABC > AbstractArtifactDefaults > AbstractBase ensures this is correct.

:obj:`AbstractBase` contains all attributes without a default. Please place any extra attributes that do not require defaults within this class. Also ensure to use `field(init=false)` for each attribute so they are not required when the class is first created.

:obj:`AbstractArtifactDefaults` provides any attributes with defaults. Also, use `field(init=False)` for each one as before.

:obj:`Artifact` is the class every artifact needs to be subclassed from.

"""

from __future__ import annotations

import abc
import contextlib
import inspect
import logging
import pathlib
import typing as t

from dataclasses import dataclass, field

import xleapp.globals as g

from xleapp import app, artifact

from .descriptors import FoundFiles, Icon, ReportHeaders, SearchRegex


if t.TYPE_CHECKING:
    from .regex import Regex


@dataclass
class AbstractBase:
    """Base class to set any properties for :obj: `Artifact` Class."""

    name: str = field(init=False)
    description: str = field(init=False, repr=False, compare=False)
    regex: set[Regex] = field(
        init=False,
        repr=False,
        compare=False,
        default=SearchRegex(),
    )
    device_type: str = field(init=False)
    device: app.Device = field(init=False)
    _log: logging.Logger = field(init=False, repr=False, compare=False)


# TODO: https://github.com/python/mypy/issues/4717
@dataclass
class AbstractArtifactDefaults:
    """Class to set defaults to any properties for the
    :obj:`Artifact` class.

    Attributes core, long_running_process, and selected are used
    to track artifacts internally for certain actions.
    """

    category: str = field(init=False, default="Unknown")
    core: bool = field(init=False, default=False)
    data: list[t.Any] = field(
        init=False,
        repr=False,
        compare=False,
        default_factory=list,
    )
    found: FoundFiles = field(init=False, default=FoundFiles(), compare=False)
    long_running_process: bool = field(init=False, default=False, compare=False)
    processed: bool = field(init=False, default=False, compare=False)
    process_time: float = field(init=False, default=float(), compare=False)
    report: bool = field(init=False, default=True, compare=False)
    report_title: str = field(init=False, default="")
    report_headers: ReportHeaders = field(init=False, default=ReportHeaders())
    select: bool = field(init=False, default=False, compare=False)
    timeline: bool = field(init=False, default=False, compare=False)
    web_icon: Icon = field(init=False, default=Icon(), compare=False)


@dataclass
class Artifact(abc.ABC, AbstractArtifactDefaults, AbstractBase):
    """Abstract class for creating Artifacts"""

    @abc.abstractmethod
    def process(self) -> None:
        """Gets artifacts located in `files_found` params by the
        `seeker`. It saves should save the report in `report_folder`.
        """

    @classmethod
    def __init_subclass__(cls, *, category, label):
        super().__init_subclass__()
        if not inspect.isabstract(cls):
            if label in app.__ARTIFACT_PLUGINS__:
                raise ValueError(f"Name {repr(label)} already registered!")

            cls.device_type = cls.__module__.split(".")[1]
            cls.name = label
            cls.category = category
            cls.device = g.app.device

            artifact = dataclass(cls, eq=False)()
            app.__ARTIFACT_PLUGINS__[label] = artifact

    def __eq__(self, __o: t.Union[str, Artifact]) -> bool:
        if isinstance(__o, str):
            return self.name == __o

        if isinstance(__o, Artifact):
            return (self.category, self.name, self.device_type) == (
                __o.category,
                __o.name,
                __o.device_type,
            )

        return False

    def __lt__(self, __o: Artifact) -> bool:
        return (self.device_type, self.category, self.name) < (
            __o.device_type,
            __o.category,
            __o.name,
        )

    @contextlib.contextmanager
    def context(self) -> t.Iterator[Artifact]:
        """Creates a context manager for an artifact.

        This will automatically search and add the regex and files to an artifact when
        called. You then can use `self.found` when processing the artifact.

        Example:
            This can be used with `with` blocks::

            >>> with Artifact.context("*/my_regex*", file_names_only=True) as artifact:
                    artifact.name = 'New Name'
                    artifact.process()

        Args:
            regex(str): regular expression to search files
            file_names_only(bool): return only file names
            return_on_first_hit(bool): return on first hit

        Yields:
            Artifact: Updated object
        """
        with contextlib.suppress(AttributeError):
            seeker = g.app.seeker

            files = seeker.file_handles

            for artifact_regex in self.regex:
                handles = None
                results = None
                regex = str(artifact_regex.regex)
                if artifact_regex.processed:
                    handles = files[regex]
                else:
                    try:
                        if artifact_regex.return_on_first_hit:
                            results = {next(seeker.search(regex))}
                        else:
                            results = set(seeker.search(regex))
                    except StopIteration:
                        results = None

                    if results:
                        files.add(artifact_regex, results, artifact_regex.file_names_only)

                    artifact_regex.processed = True

                if handles or results:
                    if artifact_regex.return_on_first_hit or len(results) == 1:
                        self.found = self.found | {files[artifact_regex].copy().pop()}
                    else:
                        self.found = self.found | files[artifact_regex]

        yield self

    @property
    def cls_name(self) -> str:
        """Returns class Name of object
        Returns:
            str: class name
        """
        return type(self).__name__

    @property
    def data_save_folder(self) -> pathlib.Path:
        """Locate to save files from this artifact

        Returns:
            Path to the folder to save files
        """
        return pathlib.Path(g.app.report_folder / "export" / self.cls_name)

    @property
    def kml(self) -> bool:
        """Checks if artifact has Lat/Long data for KML

        Returns:
            Returns true if "Timestamp", "Latitude", "Longitude" are in report headers.
        """
        if isinstance(self.report_headers, tuple):
            headers = {col.lower() for col in self.report_headers}
            return {"timestamp", "latitude", "longitude"} <= headers
        elif isinstance(self.report_headers, list):
            for table in self.report_headers:
                headers = {col.lower() for col in table}
                if {"timestamp", "latitude", "longitude"} <= headers:
                    return True
        return False

    def copyfile(
        self, input_file: pathlib.Path | bytes, output_file: str
    ) -> pathlib.Path:
        """Exports file to report folder

        File will be located under report_folder\\export\\artifact_class

        A shortcut for :func:`artifacts.copyfile()` enforcing the save
        location for each file.

        Args:
            input_file: input file name/path or :obj:`io.BytesIO`
            output_file: output file name

        Returns:
            Path: Path object of the file save location and name.
        """
        return artifact.copyfile(
            input_file=input_file,
            output_file=self.data_save_folder / output_file,
        )

    def log(self, level: int = logging.INFO, message: object = None) -> None:
        """Log message for this artifact

        Args:
            level: Logging message level. Defaults to logging.INFO.
            message: Message to log. Defaults to None.

        Raises:
            AttributeError: Error message if :attr:`message` is not set.
        """
        if not hasattr(self, "_log"):
            self._log = logging.getLogger("xleapp.logfile")

        if not message:
            raise AttributeError(f"Message missing for log on {self.cls_name}!")

        self._log.log(level, msg=message)
