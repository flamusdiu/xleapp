import typing
from collections import UserDict

if typing.TYPE_CHECKING:
    from xleapp.artifacts.abstract import AbstractArtifact


class ArtifactServiceBuilder:
    _instance: "AbstractArtifact" = None

    def __call__(self, artifact: "AbstractArtifact") -> "AbstractArtifact":
        if not self._instance:
            self._instance = artifact
        return self._instance


class ArtifactService(UserDict):
    def __init__(self) -> None:
        self.data = {}
        self._items = 0

    def __len__(self) -> int:
        return self._items

    def register_builder(self, key: str, builder: ArtifactServiceBuilder) -> None:
        self._items = self._items + 1
        self.data[key] = builder()

    def create(self, key: str) -> "AbstractArtifact":
        builder = self.data.get(key)
        if not builder:
            raise ValueError(key)

        return builder
