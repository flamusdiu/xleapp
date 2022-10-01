from __future__ import annotations

import abc
import importlib
import typing as t

from .helpers.search import FileSeekerBase, search_providers


if t.TYPE_CHECKING:
    from .artifact import Artifact, Artifacts


class Plugin(abc.ABC):
    _plugins: list[Artifact]

    def __init__(self) -> None:
        self._plugins: list = []

        for it in self.folder.glob("*.py"):
            if it.suffix == ".py" and it.stem not in ["__init__"]:
                module_name = f'{".".join(self.folder.parts[-3:])}.{it.stem}'
                importlib.import_module(module_name)

    @property
    def plugins(self) -> list[Artifact]:
        return self._plugins

    @plugins.setter
    def plugins(self, plugins: list[Artifact]) -> None:
        self._plugins = plugins

    @abc.abstractmethod
    def pre_process(self, artifacts: Artifacts) -> None:
        """Runs before artifacts are processed

        Configure this function to process artifacts ahead of :func:`Artifact.process()`
        functions running.

        Args:
            artifacts: an artifact service
        """

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
                        f"Search provider {file_seeker!r} is not a FileSeeker!",
                    )
        else:
            search_providers.register_builder(name, file_seekers)


class PluginMissingError(RuntimeError):
    """Raised when no modules are installed!"""

    pass
