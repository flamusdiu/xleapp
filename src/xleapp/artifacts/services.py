from __future__ import annotations

import itertools
import logging
import typing as t

from dataclasses import dataclass
from enum import Enum
from queue import PriorityQueue

import PySimpleGUI as PySG
import wrapt

from ..helpers.decorators import timed
from ..helpers.strings import split_camel_case


_T = t.TypeVar("_T")

if t.TYPE_CHECKING:
    from ..app import Application
    from ..gui.utils import ProcessThread
    from ..plugins import Plugin

logger_log = logging.getLogger("xleapp.logfile")


class ArtifactProxy(wrapt.ObjectProxy):
    """Object proxy to support hashing :obj:`ArtifactEnum`"""

    def __hash__(self) -> int:
        return hash((self.__wrapped__.name, self.__wrapped__.category))


class ArtifactError(Exception):
    """Basic exception for Artifacts"""

    pass


class ArtifactEnum(Enum):
    """Enum for Artifacts

    This class holds all the installed artifacts in a :obj:`enum` for search searching
    and modifying of artifact attributes.
    """

    def __lt__(self, other: ArtifactEnum) -> bool:
        return self.name < other.name

    def __getattr__(self, name: str) -> t.Any:
        """Wraps the :attr:`_value_` of the Enum object.

        Attributes can be assessed through dot notation `X.name` which will check the
        Enum.value for the property and return that property.

        Meaning that:
            X.name == X.value.name

        Args:
            name: Name of the property.

        Raises:
            AttributeError: If property does not exists.

        Returns:
            Any: Returns the value of the property which could be anything.
        """
        if "_value_" in self.__dict__.keys() and hasattr(self.value, name):
            return getattr(self.value, name)
        elif name in self.__dict__:
            return self.__dict__[name]
        else:
            raise AttributeError(
                f"{__name__!r} doesn't have {name!r} attribute",
            ) from None

    def process(self) -> None:
        """Processes and log the artifact"""
        msg_artifact = f"{self.value.category} [{self.cls_name}] artifact"
        logger_log.info(f"\n{msg_artifact} processing...")
        self.value.process_time, _ = timed(self.value.process)()
        if not self.value.processed:
            logger_log.warn("-> Failed to processed!")
        logger_log.info(f"{msg_artifact} finished in {self.value.process_time:.2f}s")


class Artifacts:
    """Service controlling all the artifacts

    Attributes:
        data: Enum for artifacts for this service
        app: Application instance attached to this service
        queue: Priority queue for processing the artifacts.
    """

    data: ArtifactEnum
    app: Application
    queue: PriorityQueue

    def __init__(self, app: Application) -> None:
        self.app = app
        if "Type" in self.app.device:
            self = self(self.app.device["Type"])

    def __call__(self, device_type: str) -> Artifacts:
        """Updates the :attr:`data` for artifacts for the :attr:`device_type`.

        Args:
            device_type: type of device being parsed

        Returns:
            Artifacts: updated service object
        """
        self.queue = PriorityQueue()
        self.data = Artifacts.generate_artifact_enum(
            app=self.app,
            device_type=device_type,
        )
        for artifact in self.data:
            priorty = 10
            if artifact.core:
                priorty = 1
            self.queue.put((priorty, artifact))
        return self

    def __getattr__(self, name: str) -> t.Any:
        try:
            if name != "data":
                return getattr(self.data, name)
        except AttributeError:
            raise AttributeError(
                f"{__name__!r} doesn't have {name!r} attribute",
            ) from None

    def __getitem__(self, name: str) -> ArtifactEnum:
        return getattr(self.data, name)

    def __len__(self) -> int:
        return len(self.data) or 0

    @property
    def installed(self) -> list[str]:
        """Returns the list of installed artifacts

        Returns:
            The list of artifacts.
        """
        return [artifact.cls_name for artifact in self.data]

    @property
    def selected(self) -> list[str]:
        """Returns the list of selected artifacts for processing

        Returns:
            The list of selected artifacts.
        """
        return [artifact.cls_name for artifact in self.data if artifact.select]

    def reset(self) -> None:
        """Resets the list of selected artifacts."""
        for artifact in self.data:
            if not artifact.core:
                artifact.selected = False

    def select(
        self,
        *artifacts: str,
        selected: t.Optional[bool] = True,
        long_running_process: t.Optional[bool] = False,
        all: t.Optional[bool] = False,
    ) -> None:
        """Selects one or more artifacts to be processed.

        Args:
            selected: Boolean to select or deselect an artifact. Defaults to True.
            long_running_process: Select long running processes. Use the
                :func:`@long_running_process` decorator to mark it as 'long_running_process'. Defaults to False.
            all: Select all artifacts except 'long_running_processes'. To select long running processing set both :attr:`long_running_process` and :attr:`all` to True. Defaults to False.

        Raises:
            KeyError: Raises error if artifact does not exists.
        """
        if all:
            for artifact in self.data:
                if not artifact.core:
                    if not long_running_process and artifact.long_running_process:
                        artifact.select = False
                    else:
                        artifact.select = True

        for item in artifacts:
            try:
                self.data[item].select = selected
            except KeyError:
                raise KeyError(f"Artifact[{item!r}] does not exist!")

    @staticmethod
    def generate_artifact_enum(
        app: Application,
        device_type: str,
    ) -> t.Type[ArtifactEnum]:
        """Generates a Enumeration object for all artifacts based on supplied device type.

        Args:
            app: Application object to attached to each artifact
            device_type: type of device being processed

        Returns:
            An Enumeration.
        """
        members = {}
        plugins: Plugin = list(app.plugins[device_type])[0]
        for xleapp_cls in plugins.plugins:
            artifact = dataclass(
                xleapp_cls,
            )()
            artifact_name = "_".join(
                split_camel_case(artifact.cls_name),
            ).upper()
            artifact.app = app  # ignore

            artifact_proxy = ArtifactProxy(artifact)
            members[artifact_proxy] = [
                artifact_name,
                artifact.cls_name,
            ]

        return t.cast(
            t.Type[ArtifactEnum],
            Enum(
                value="ArtifactEnum",
                names=itertools.chain.from_iterable(
                    itertools.product(v, [k]) for k, v in members.items()
                ),
                module=__name__,
                type=ArtifactEnum,
            ),
        )

    def crunch_artifacts(
        self,
        window: PySG.Window = None,
        thread: ProcessThread = None,
    ) -> None:
        """Processes all the selected artifacts

        Args:
            window: :mod:`PySimpleGUI` window when running the GUI. Defaults to None.
            thread: :mod:`threading` instance for processing artifacts. Defaults to None.
        """
        num_processed = 0
        artifact: ArtifactEnum
        device_type: str = self.app.device["Type"]
        plugins: Plugin = list(self.app.plugins[device_type])[0]

        if hasattr(plugins, "pre_process"):
            plugins.pre_process(self)

        if window:
            window["<PROGRESSBAR>"].update(0, self.app.num_to_process)

        while not self.queue.empty():
            if thread and thread.stopped:
                break

            _, artifact = self.queue.get()

            if not artifact.select:
                self.queue.task_done()
                continue

            artifact.process()
            num_processed += 1
            if window:
                window.write_event_value("<THREAD>", num_processed)
            self.queue.task_done()
        if window and not thread.stopped:
            window.write_event_value("<DONE>", None)
