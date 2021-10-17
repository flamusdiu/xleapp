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

logger_log = logging.getLogger("xleapp.logfile")


class ArtifactError(Exception):
    pass


class Artifact:
    def __getattr__(self, name: str) -> t.Any:
        if "_value_" in self.__dict__.keys():
            if hasattr(self.value, name):
                return getattr(self.value, name)
        if name in self.__dict__:
            return self.__dict__[name]
        else:
            raise AttributeError(
                f"{__name__!r} doesn't have {name!r} attribute",
            ) from None

    def __contains__(cls, item):
        try:
            cls.value[item]
        except ValueError:
            return False
        else:
            return True

    def process(self) -> None:
        msg_artifact = f"{self.value.category} [{self.cls_name}] artifact"
        logger_log.info(f"\n{msg_artifact} processing...")
        self.value.process_time, _ = self.value.process()
        if not self.value.processed:
            logger_log.warn("-> Failed to processed!")
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
                f"{__name__!r} doesn't have {name!r} attribute",
            ) from None

    def __iter__(self):
        for artifact in self.data:
            yield artifact

    def __getitem__(self, name):
        return getattr(self.data, name)

    def __contains__(cls, item):
        try:
            cls.data[item]
        except ValueError:
            return False
        else:
            return True

    @property
    def installed(self) -> list:
        return [artifact.cls_name for artifact in self]

    @property
    def selected(self) -> list:
        return [artifact.cls_name for artifact in self if artifact.select]

    def reset(self):
        for artifact in self.data:
            if not artifact.core:
                artifact.selected = False

    def select(
        self,
        *artifacts,
        selected: t.Optional[bool] = True,
        long_running_process: t.Optional[bool] = False,
        all: t.Optional[bool] = False,
    ) -> None:
        if all:
            for artifact in self:
                if not artifact.core:
                    if not long_running_process and artifact.long_running_process:
                        artifact.select = False
                    else:
                        artifact.select = True

        for item in artifacts:
            try:
                self[item].select = selected
            except KeyError:
                raise KeyError(f"Artifact[{item!r}] does not exist!")

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
                    for _, xleapp_cls in module_members:
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
                                xleapp_cls,
                                unsafe_hash=True,
                            )()
                            artifact_name = "_".join(
                                split_camel_case(artifact.cls_name),
                            ).upper()
                            artifact.app = app
                            members[artifact] = [
                                artifact_name,
                                artifact.cls_name,
                            ]

        return Enum(
            value=f"{device_type.title()}Artifact",
            names=itertools.chain.from_iterable(
                itertools.product(v, [k]) for k, v in members.items()
            ),
            module=__name__,
            type=Artifact,
        )
