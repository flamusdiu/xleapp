from __future__ import annotations

import functools
import logging
import queue
import typing as t

from plistlib import InvalidFileException

import PySimpleGUI as PySG

from xleapp.helpers.decorators import timed
from xleapp.helpers.types import DecoratedFunc


if t.TYPE_CHECKING:
    from xleapp import Artifact
    from xleapp.gui import ProcessThread
    from xleapp.plugins import Plugin

logger_log = logging.getLogger("xleapp.logfile")


def artifact_process(cls: DecoratedFunc) -> DecoratedFunc:
    @functools.wraps(cls)
    def process_wrapper() -> None:
        msg_artifact = f"{cls.category} [{cls.cls_name}] artifact"
        logger_log.info(f"\n{msg_artifact} processing...")
        try:
            cls.process_time, _ = process_wrapper.orig_func()
        except InvalidFileException as err:
            logger_log.warn(f"-> {err}")
            cls.processed = False

        if not cls.processed:
            logger_log.warn("-> Failed to processed!")
        logger_log.info(f"{msg_artifact} finished in {cls.process_time:.2f}s")

    process_wrapper.orig_func = timed(cls.process)
    return t.cast(DecoratedFunc, process_wrapper)


class ArtifactError(Exception):
    """Basic exception for Artifacts"""

    pass


class Artifacts:

    __slots__ = ("_store", "process_queue", "_processing_device_type")

    def __init__(self) -> None:
        self._store: list = list()
        self.process_queue: queue.PriorityQueue = queue.PriorityQueue()
        self._processing_device_type = None

    def __getitem__(self, __key: str) -> Artifact:
        for artifact in self._store:
            if artifact.cls_name.lower() == __key.lower():
                return artifact
        raise ValueError(f"Artifact '{__key}' not found in artifact service!")

    def __setitem__(self, __key: str, __value: Artifact) -> None:
        if __key in self:
            raise ValueError(f"Artifact '{__key}' already registered!")
        self._store.append(__value)

    def __delitem__(self, __key: str) -> None:
        for artifact in self._store:
            if artifact.cls_name.lower() == __key:
                self._store.remove[artifact]

    def __iter__(self) -> t.Iterator[str, Artifact]:
        return iter(self._store)

    def __len__(self) -> int:
        return len(self)

    def __repr__(self) -> str:
        return "Artifacts()"

    def __str__(self) -> str:
        artifact_lst = {artifact.name for artifact in self._store}
        return (
            "Artifacts service contains the following artifacts: "
            f"{'; '.join(artifact_lst)}. Process queue contains "
            f"{len(self.process_queue)!r} artifacts to be processed!"
        )

    @property
    def processing_device_type(self) -> str:
        return self._processing_device_type

    @processing_device_type.setter
    def processing_device_type(self, device_type: str):
        self._processing_device_type = device_type
        self.reset()

        for artifact in self:
            if artifact.core and artifact.device_type == device_type:
                artifact.select

    def create_queue(self):
        for artifact in self:
            priority = 10
            if artifact.core:
                priority = 1

            priority = getattr(artifact, "priority", None) or priority

            artifact.process = artifact_process(artifact)
            self.process_queue.put((priority, artifact))

    def run_queue(
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
        plugins: Plugin = self.selected()

        if hasattr(plugins, "pre_process"):
            plugins.pre_process(self)

        if window:
            window["<PROGRESSBAR>"].update(0, self.app.num_to_process)

        while not self.process_queue.empty():
            if thread and thread.stopped:
                break

            _, artifact = self.process_queue.get()

            if not artifact.select:
                self.process_queue.task_done()
                continue

            artifact.process()
            num_processed += 1
            if window:
                window.write_event_value("<THREAD>", num_processed)
            self.process_queue.task_done()
        if window and not thread.stopped:
            window.write_event_value("<DONE>", None)

    def toggle_artifact(self, name: str):
        """Selects/Deselects artifact for processing

        Args:
            name (str): Artifact to be selected/deselected.
        """
        artifact = self[name]
        if not artifact.core:
            artifact.select = not artifact.select

    def installed(self) -> list[str]:
        """Returns the list of installed artifacts

        Returns:
            The list of artifacts
        """

        return sorted({artifact.name for artifact in self})

    def installed_categories(self) -> list[str]:
        """Returns the list of installed artifact categories

        Returns:
            The list of artifacts
        """

        return sorted({artifact.category for artifact in self})

    def selected(self) -> set[str]:
        """Returns the list of selected artifacts for processing

        Returns:
            The list of selected artifacts.
        """
        return list(
            filter(
                lambda artifact: artifact.select
                and (
                    artifact.device_type == self.processing_device_type
                    or not self.processing_device_type
                ),
                self,
            )
        )

    def reset(self) -> None:
        """Resets the list of selected artifacts."""
        for artifact in self:
            if not artifact.core and not (
                artifact.device_type == self.processing_device_type
            ):
                artifact.select = False
            elif artifact.core and (artifact.device_type == self.processing_device_type):
                artifact.select = True
