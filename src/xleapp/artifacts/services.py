from __future__ import annotations

import collections.abc as abc
import inspect
import logging
import queue
import typing as t

import PySimpleGUI as PySG
import xleapp.globals as g


if t.TYPE_CHECKING:
    from ..artifacts import Artifact
    from ..gui import ProcessThread
    from ..plugins import Plugin

logger_log = logging.getLogger("xleapp.logfile")


class ArtifactError(Exception):
    """Basic exception for Artifacts"""

    pass


class Artifacts(abc.MutableMapping):
    __slots__ = ("store", "queue")
    store: dict
    queue: queue.PriorityQueue

    def __init__(self):
        self.store = dict()
        self.queue = queue.PriorityQueue()

    def __getitem__(self, __key: str) -> Artifact:
        artifact = self.store[__key]
        if inspect.isabstract(artifact):
            artifact = artifact()
            self.store[__key] = artifact
            return artifact
        return artifact

    def __setitem__(self, __key: str, __value: Artifact) -> None:
        if __key in self:
            ValueError(f"Artifact '{__key}' already registered!")
        self.store[__key] = __value

    def __delitem__(self, __key: str) -> None:
        del self.store[__key]

    def __iter__(self) -> t.Iterator[str, Artifact]:
        return iter(self.store.items())

    def __len__(self) -> int:
        return len(self)

    def __repr__(self):
        return repr(self)

    def create_queue(self):
        for _, artifact in self:
            priority = 10
            if artifact.core:
                priority = 1

            priority = artifact.priority or priority
            self.queue.put((priority, artifact))

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
        device_type: str = g.app.device["Type"]
        plugins: Plugin = list(g.app.plugins[device_type])[0]

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

    @property
    def installed(self) -> list[str]:
        """Returns the list of installed artifacts

        Returns:
            The list of artifacts
        """

        return [artifact.cls_name for artifact in self.store]

    @property
    def selected(self) -> list[str]:
        """Returns the list of selected artifacts for processing

        Returns:
            The list of selected artifacts.
        """
        return [artifact.cls_name for artifact in self.store if artifact.select]

    def reset(self) -> None:
        """Resets the list of selected artifacts."""
        for artifact in self.store:
            if not artifact.core:
                artifact.selected = False
