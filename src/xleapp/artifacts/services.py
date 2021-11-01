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
    from ..app import XLEAPP
    from ..gui.utils import ProcessThread
    from ..plugins import Plugin

logger_log = logging.getLogger("xleapp.logfile")


class ArtifactProxy(wrapt.ObjectProxy):
    def __hash__(self):
        return hash((self.__wrapped__.name, self.__wrapped__.category))


class ArtifactError(Exception):
    pass


class ArtifactEnum(Enum):
    def __lt__(self, other):
        return self.name < other.name

    def __getattr__(self, name: str) -> t.Any:
        if "_value_" in self.__dict__.keys() and hasattr(self.value, name):
            return getattr(self.value, name)
        elif name in self.__dict__:
            return self.__dict__[name]
        else:
            raise AttributeError(
                f"{__name__!r} doesn't have {name!r} attribute",
            ) from None

    def process(self) -> None:
        msg_artifact = f"{self.value.category} [{self.cls_name}] artifact"
        logger_log.info(f"\n{msg_artifact} processing...")
        self.value.process_time, _ = timed(self.value.process)()
        if not self.value.processed:
            logger_log.warn("-> Failed to processed!")
        logger_log.info(f"{msg_artifact} finished in {self.value.process_time:.2f}s")


class Artifacts:

    data: ArtifactEnum
    app: "XLEAPP"
    queue: PriorityQueue

    def __init__(self, app: "XLEAPP") -> None:
        self.app = app
        if "type" in self.app.device:
            self = self(self.app.device["type"])

    def __call__(self, device_type: str) -> "Artifacts":
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
        return [artifact.cls_name for artifact in self.data]

    @property
    def selected(self) -> list[str]:
        return [artifact.cls_name for artifact in self.data if artifact.select]

    def reset(self) -> None:
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
    def generate_artifact_enum(app: "XLEAPP", device_type: str) -> t.Type[ArtifactEnum]:
        members = {}
        plugins: "Plugin" = list(app.plugins[device_type])[0]
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
        thread: "ProcessThread" = None,
    ) -> None:
        num_processed = 0
        artifact: ArtifactEnum
        device_type: str = self.app.device["type"]
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
