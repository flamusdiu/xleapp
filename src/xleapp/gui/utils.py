import threading
import typing as t

from abc import ABC, abstractmethod
from contextlib import suppress

import PySimpleGUI as PySG


if t.TYPE_CHECKING:
    from xleapp.app import XLEAPP


class ProcessThread(ABC, threading.Thread):
    def __init__(
        self,
        app: "XLEAPP",
        window: PySG.Window = None,
        sleep_time: int = 0.1,
        daemon=True,
    ):
        self._stop_event = threading.Event()
        self._sleep_time = sleep_time
        self._app = app
        self._window = window
        super().__init__(daemon=True)

    @abstractmethod
    def run(self):
        NotImplementedError("Need to define a run method!")

    @property
    def stopped(self) -> bool:
        return self._stop_event.is_set()

    def join(self, timeout=None):
        self._stop_event.set()
        super().join(timeout)


class ArtifactProcessor(ProcessThread):
    def run(self):
        self._app.crunch_artifacts(self._window, self)


def disable_widgets(window: PySG.Window, disabled: bool = False):
    for widget in window.key_dict.keys():
        if str(widget).startswith("-") and str(widget).endswith("-"):
            # Widget does not have an update function. Just ignore error.
            with suppress(TypeError):
                window[f"{widget}"].update(
                    disabled=disabled,
                )
    window.refresh()
