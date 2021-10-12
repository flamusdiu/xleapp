import logging
import typing as t
from collections import UserDict
from functools import cached_property

if t.TYPE_CHECKING:
    from ._abstract import Artifact

logger_log = logging.getLogger("xleapp.logfile")


class ArtifactServiceBuilder:
    _instance: "Artifact"

    def __init__(self, artfact: "Artifact"):
        self._instance = artfact

    def __call__(self, artifact: "Artifact") -> "Artifact":
        if not self._instance:
            self._instance = artifact
        return self._instance

    def __get__(self):
        return self._instance


class ArtifactService(UserDict):
    def __len__(self) -> int:
        return len(self.data)

    def register_builder(self, key: str, cls: "Artifact") -> None:
        self[key] = ArtifactServiceBuilder(cls)

    @cached_property
    def installed(self) -> list:
        return [name.lower() for name in self.keys()]

    @property
    def selected(self) -> list:
        return [name for name, artifact in self.items() if artifact.selected]

    def select_artifact(
        self,
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
            self.get(name).selected ^= True
        else:
            for artifact in list(self.values()):
                if reset:
                    if not artifact.core:
                        artifact.selected = False
                elif all_artifacts:
                    if artifact.long_running_process and not artifact.core:
                        if long_running_process:
                            artifact.selected = False
                    elif not artifact.core:
                        artifact.selected = not artifact.selected

    def process_artifact(self, artifact: "Artifact") -> None:
        msg_artifact = f"{artifact.category} [{artifact.cls_name}] artifact"
        logger_log.info(f"\n{msg_artifact} processing...")
        artifact.process_time, _ = artifact.process()
        if not artifact.processed:
            logger_log.warn(f"-> Artifact failed to processed!")
        logger_log.info(f"{msg_artifact} finished in {artifact.process_time:.2f}s")
