
import importlib
import inspect

from abc import ABC, abstractmethod
from pathlib import Path

from xleapp.artifacts.services import Artifacts


class Plugin(ABC):

    def __init__(self) -> None:
        self.plugins = []

        for it in self.folder.glob("*.py"):
            if it.suffix == ".py" and it.stem not in ["__init__"]:
                module_name = f'{".".join(self.folder.parts[-2:])}.{it.stem}'
                module = importlib.import_module(module_name)
                module_members = inspect.getmembers(module, inspect.isclass)
                for _, xleapp_cls in module_members:
                    # check MRO (Method Resolution Order) for
                    # Artifact classes. Also, insure
                    # we do not get an abstract class.
                    artifact_mro = (
                        {str(name).find("Artifact") for name in xleapp_cls.mro()}
                    )

                    if (
                        len(artifact_mro - {-1}) != 0
                        and not inspect.isabstract(xleapp_cls)
                    ):
                        self.plugins.append(xleapp_cls)

    @property
    def plugins(self) -> list:
        return self._plugins

    @plugins.setter
    def plugins(self, value) -> None:
        self._plugins = value

    @property
    @abstractmethod
    def folder(self) -> Path:
        """Returns path to plugins folder

        Basic usage is shown here. This needs to be in plugin's concret class to
        get proper path.

        Example:
            @property
            def folder(self) -> Path:
                return Path(__file__).parent
        """
        NotImplementedError('Need to implement the `folder()` method!')

    @abstractmethod
    def pre_process(self, artifacts: Artifacts) -> None:
        NotImplementedError('Need to implement the pre_process_artifact()!')
