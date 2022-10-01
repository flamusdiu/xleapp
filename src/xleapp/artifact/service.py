from __future__ import annotations

import logging
import queue
import typing as t

import PySimpleGUI as PySG
import xleapp.globals as g


if t.TYPE_CHECKING:
    from xleapp import Artifact
    from xleapp.gui import ProcessThread
    from xleapp.plugins import Plugin

logger_log = logging.getLogger("xleapp.logfile")


class ArtifactError(Exception):
    """Basic exception for Artifacts"""

    pass


class Artifacts:
    __slots__ = ("store", "process_queue")

    def __init__(self) -> None:
        self.store: list = list()
        self.process_queue: queue.PriorityQueue = queue.PriorityQueue()

    def __getitem__(self, __key: str) -> Artifact:
        for artifact in self.store:
            if artifact.name == __key:
                break
        return artifact

    def __setitem__(self, __key: str, __value: Artifact) -> None:
        if __key in self:
            ValueError(f"Artifact '{__key}' already registered!")
        self.store.append(__value)

    def __delitem__(self, __key: str) -> None:
        for artifact in self.store:
            if artifact.name == __key:
                self.store.remove[artifact]

    def __iter__(self) -> t.Iterator[str, Artifact]:
        return iter(self.store)

    def __len__(self) -> int:
        return len(self)

    def __repr__(self) -> str:
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

        return [artifact.name for artifact in self.store]

    @property
    def selected(self) -> set[str]:
        """Returns the list of selected artifacts for processing

        Returns:
            The list of selected artifacts.
        """
        selected_artifacts = set()
        for artifact in self.store:
            if artifact.select:
                selected_artifacts.add(artifact.name)
        return selected_artifacts

    def reset(self) -> None:
        """Resets the list of selected artifacts."""
        for artifact in self.store:
            if not artifact.core:
                artifact.selected = False
