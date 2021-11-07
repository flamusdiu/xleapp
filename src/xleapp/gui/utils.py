import threading
import typing as t

from abc import ABC, abstractmethod
from contextlib import suppress

import PySimpleGUI as PySG


if t.TYPE_CHECKING:
    from xleapp.app import Application


class ProcessThread(ABC, threading.Thread):
    """Thread for processing artifacts

    Args:
        app: application instance.
        window: GUI window the thread is attached to. Defaults to None.
        sleep_time: how long to sleep between checking the thread. Defaults to 0.1.
        daemon: marks if the thread runs as a daemon. Defaults to True.
    """

    def __init__(
        self,
        app: "Application",
        window: PySG.Window = None,
        sleep_time: float = 0.1,
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
        """Checks if the thread should be stopped."""
        return self._stop_event.is_set()

    def join(self, timeout=None):
        """Joins a thread to ensures it stopped running when the :attr:`_stop_event` is set.

        Args:
            timeout: Sets the timeout to wait on :func:`thread.join()`. Defaults to None.
        """
        self._stop_event.set()
        super().join(timeout)


class ArtifactProcessor(ProcessThread):
    """Creates a thread to process the artifacts"""

    def run(self):
        self._app.crunch_artifacts(self._window, self)


def disable_widgets(window: PySG.Window, disabled: bool = False):
    """Disables/Enables all widgets in the GUI.

    Note:
        Widgets are only disabled if the key is similar to "-KEY-".

    Args:
        window: The GUI window to disable widgets for.
        disabled: Boolean to disable/enable widgets. Defaults to False.
    """
    for widget in window.key_dict:
        if str(widget).startswith("-") and str(widget).endswith("-"):
            # Widget does not have an update function. Just ignore error.
            with suppress(TypeError):
                window[f"{widget}"].update(
                    disabled=disabled,
                )
    window.refresh()
