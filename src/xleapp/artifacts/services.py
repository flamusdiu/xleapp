import importlib
import inspect
import itertools
import logging
import typing as t

from dataclasses import dataclass
from enum import Enum
from importlib.metadata import entry_points
from pathlib import Path

from xleapp.helpers.strings import split_camel_case


if t.TYPE_CHECKING:
    from xleapp.app import XLEAPP

    from ._abstract import Artifact

logger_log = logging.getLogger("xleapp.logfile")


class Artifact:
    @property
    def cls_name(self) -> str:
        return self.value.cls_name.lower()

    @property
    def core(self) -> bool:
        return self.value.core

    @property
    def long_running_process(self) -> bool:
        return self.value.long_running_process

    @property
    def selected(self) -> bool:
        return self.value._selected

    @selected.setter
    def selected(self, bool: bool = True) -> None:
        """Toggles the selected state of the artifact

        Note:
            True fips the toggle state. i.e. `selected` property is changed from True
            to False or from False to True. False keeps the current state.

        Args:
            bool (bool, optional): Selected state of the artifact. Defaults to True.
        """
        if not self.core:
            self.value._selected ^= bool

    def process_artifact(self) -> None:
        msg_artifact = f"{self.value.category} [{self.cls_name}] artifact"
        logger_log.info(f"\n{msg_artifact} processing...")
        self.value.process_time, _ = self.value.process()
        if not self.value.processed:
            logger_log.warn(f"-> Artifact failed to processed!")
        logger_log.info(f"{msg_artifact} finished in {self.value.process_time:.2f}s")


class Artifacts:

    data: Enum

    def __init__(self, app: "XLEAPP") -> None:
        self.data = Artifacts.generate_artifact_enum(app)

    def __getattr__(self, name: str) -> t.Any:
        try:
            return getattr(self.data, name)
        except AttributeError:
            raise AttributeError(
                f"{__name__!r} doesn't have {name!r} attribute"
            ) from None

    @property
    def installed(self) -> list:
        return [artifact.cls_name for artifact in self]

    @property
    def selected_artifacts(self) -> list:
        return [artifact.cls_name for artifact in self.data if artifact.selected]

    def reset_selected(self):
        for artifact in self.data:
            if not artifact.core:
                artifact.selected = False

    def select_all(
        self,
        long_running_process: t.Optional[bool] = False,
    ) -> None:
        for artifact in self.data:
            if not artifact.core:
                if not long_running_process and artifact.long_running_process:
                    artifact.selected = False
                else:
                    artifact.selected = True

    @staticmethod
    def generate_artifact_enum(app: "XLEAPP"):
        members = {}
        device_type: str = app.device["type"]
        discovered_plugins = [
            plugin
            for plugin in entry_points()["xleapp.plugins"]
            if plugin.name == device_type
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
                            artifact: "Artifact" = dataclass(
                                xleapp_cls, unsafe_hash=True
                            )()
                            artifact_name = "_".join(
                                split_camel_case(artifact.cls_name)
                            ).upper()
                            artifact.app = app
                            members[artifact] = [
                                artifact_name,
                                artifact.cls_name.lower(),
                            ]

        return Enum(
            value=f"{device_type.title()}Artifact",
            names=itertools.chain.from_iterable(
                itertools.product(v, [k]) for k, v in members.items()
            ),
            module=__name__,
            type=Artifact,
        )
