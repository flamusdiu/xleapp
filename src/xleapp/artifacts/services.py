import importlib
import inspect
import logging
from dataclasses import dataclass
import typing as t
from enum import Enum
from functools import cached_property
from importlib.metadata import entry_points
from pathlib import Path
import itertools

from xleapp.helpers.strings import split_camel_case

if t.TYPE_CHECKING:
    from ._abstract import Artifact
    from xleapp.app import XLEAPP

logger_log = logging.getLogger("xleapp.logfile")


class Artifact:
    @classmethod
    @cached_property
    def installed(cls) -> list:
        return [artifact.cls_name for artifact in cls]

    @property
    def cls_name(self) -> str:
        return self.value.cls_name.lower()

    @classmethod
    @property
    def selected(cls) -> list:
        return [artifact.cls_name for artifact in cls if artifact.value.selected]

    @classmethod
    def select_artifact(
        cls,
        name: t.Optional[None] = None,
        all_artifacts: t.Optional[bool] = False,
        long_running_process: t.Optional[bool] = False,
        reset: t.Optional[bool] = False,
    ) -> None:
        """Toggles if an artifact should be run

        Core artifacts cannot be toggled. `all_artifacts` will not select any
        artifact marked as long running unless it also is set to True.

        If you want to ensure the state of the artifacts, call this with
        `reset=True` to reset all the states to their default values.

        Args:
            artifacts(List[object]): installed list of artifacts
            artifact_name (str): short name of the artifact. Defaults to None.
            all_artifacts (bool): bool to select all artifacts.
                Defaults to False.
            long_running_process (bool): used with `all_artifacts`
                to select long running processes. Defaults to False.
            reset (bool): clears the select flags on non-core artifacts.
                Defaults to True.
        """
        if name:
            cls[name].value.selected ^= True
        else:
            for artifact in cls:
                if artifact.core:
                    continue

                if reset:
                    artifact.selected = False
                elif all_artifacts:
                    if not long_running_process and artifact.long_running_process:
                        artifact.selected = False
                    else:
                        artifact.selected ^= True

    def process_artifact(self) -> None:
        msg_artifact = f"{self.value.category} [{self.cls_name}] artifact"
        logger_log.info(f"\n{msg_artifact} processing...")
        self.value.process_time, _ = self.value.process()
        if not self.value.processed:
            logger_log.warn(f"-> Artifact failed to processed!")
        logger_log.info(f"{msg_artifact} finished in {self.value.process_time:.2f}s")


def generate_artifact_enum(app: "XLEAPP"):
    members = {}
    discovered_plugins = [
        plugin
        for plugin in entry_points()["xleapp.plugins"]
        if plugin.name == app.device["type"]
    ]

    for plugin in discovered_plugins:
        # Plugins return a str which is the plugin direction to
        # find plugins inside of. This direction is loading
        # that directory. Then, all the plugins are loaded.
        module_dir = Path(plugin.load()())

        for it in module_dir.glob("*.py"):
            if it.suffix == ".py" and it.stem not in ["__init__"]:
                module_name = f'{".".join(module_dir.parts[-2:])}.{it.stem}'
                module = importlib.import_module(module_name)
                module_members = inspect.getmembers(module, inspect.isclass)
                for name, xleapp_cls in module_members:
                    # check MRO (Method Resolution Order) for
                    # Artifact classes. Also, insure
                    # we do not get an abstract class.
                    if (
                        len(
                            {str(name).find("Artifact") for name in xleapp_cls.mro()}
                            - {-1},
                        )
                        != 0
                        and not inspect.isabstract(xleapp_cls)
                    ):
                        artifact: "Artifact" = dataclass(xleapp_cls, unsafe_hash=True)()
                        artifact_name = "_".join(
                            split_camel_case(artifact.cls_name)
                        ).upper()
                        artifact.app = app
                        members[artifact] = [artifact_name, artifact.cls_name.lower()]

    return Enum(
        value="Artifact",
        names=itertools.chain.from_iterable(
            itertools.product(v, [k]) for k, v in members.items()
        ),
        module=__name__,
        type=Artifact,
    )
