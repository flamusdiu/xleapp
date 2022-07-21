from __future__ import annotations

import importlib
import inspect
import typing as t

from abc import ABC, abstractmethod
from pathlib import Path

from .helpers.search import FileSeekerBase, search_providers


if t.TYPE_CHECKING:
    from .artifacts import Artifact, Artifacts


class Plugin(ABC):
    _plugins: list[Artifact]

    def __init__(self) -> None:
        self._plugins: list = []

        for it in self.folder.glob("*.py"):
            if it.suffix == ".py" and it.stem not in ["__init__"]:
                module_name = f'{".".join(self.folder.parts[-2:])}.{it.stem}'
                module = importlib.import_module(module_name)
                module_members = inspect.getmembers(module, inspect.isclass)
                for _, xleapp_cls in module_members:
                    # check MRO (Method Resolution Order) for
                    # Artifact classes. Also, insure
                    # we do not get an abstract class.
                    artifact_mro = {
                        str(name).find("Artifact") for name in xleapp_cls.mro()
                    }

                    if len(artifact_mro - {-1}) != 0 and not inspect.isabstract(
                        xleapp_cls,
                    ):
                        self.plugins.append(xleapp_cls)

    @property
    def plugins(self) -> list[Artifact]:
        return self._plugins

    @plugins.setter
    def plugins(self, plugins: list[Artifact]) -> None:
        self._plugins = plugins

    @property
    @abstractmethod
    def folder(self) -> Path:
        """Returns path to plugins folder

        Basic usage is shown here. This needs to be in plugin's concrete class to
        get proper path.

        Example:
            @property
            def folder(self) -> Path:
                return Path(__file__).parent
        """
        raise NotImplementedError("Need to implement the `folder()` method!")

    @abstractmethod
    def pre_process(self, artifacts: Artifacts) -> None:
        """Runs before artifacts are processed

        Configure this function to process artifacts ahead of :func:`Artifact.process()`
        functions running.

        Args:
            artifacts: an artifact service
        """
        raise NotImplementedError("Need to implement the pre_process_artifact()!")

    def register_seekers(
        self,
        name: str,
        file_seekers: t.Union[FileSeekerBase, t.Sequence[FileSeekerBase]],
    ) -> None:
        """Optional function to add FileSeekers for specific plugins

        Args:
            name: name of the seeker
            file_seeker: a :obj:`FileSeekerBase` to search for files
        """
        name = name.upper()
        if isinstance(file_seekers, t.Sequence):
            for file_seeker in file_seekers:
                if isinstance(file_seeker, FileSeekerBase):
                    search_providers.register_builder(name, file_seeker)
                else:
                    raise TypeError(
                        f"Search provider {file_seeker!r} is not a FileSeeker!"
                    )
        else:
            search_providers.register_builder(name, file_seekers)
