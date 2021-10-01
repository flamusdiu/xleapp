import importlib
import inspect
import logging
import typing
from collections import UserDict
from importlib.metadata import entry_points
from pathlib import Path
from textwrap import TextWrapper
from typing import Dict, List, Type

import prettytable

from xleapp.artifacts.abstract import AbstractArtifact
from xleapp.artifacts.services import ArtifactService, ArtifactServiceBuilder

logger = logging.getLogger(__name__)

__all__ = [
    "generate_artifact_table",
    "generate_artifact_path_list",
    "generate_report",
    "crunch_artifacts",
    "select",
    "services",
    "installed",
]


def _build_artifact_list():
    """Generates a List of Artifacts installed

    Returns:
        Artifacts: dictionary of artifacts with short names as keys
    """

    logger.debug(
        "Generating artifact lists from file system...",
        extra={"flow": "no_filter"},
    )

    discovered_plugins = entry_points()['xleapp.plugins']

    for plugin in discovered_plugins:
        # Plugins return a str which is the plugin direction to
        # find plugins inside of. This direction is loading
        # that directory. Then, all the plugins are loaded.
        module_dir = Path(plugin.load()())

        for it in module_dir.glob("*.py"):
            if it.suffix == ".py" and it.stem not in ["__init__"]:
                module_name = f'{".".join(module_dir.parts[-2:])}.{it.stem}'
                module = importlib.import_module(module_name, inspect.isfunction)
                module_members = inspect.getmembers(module, inspect.isclass)
                for name, cls in module_members:
                    # check MRO (Method Resolution Order) for
                    # AbstractArtifact classes. Also, insure
                    # we do not get an abstract class.
                    if (
                        len(
                            {str(name).find("AbstractArtifact") for name in cls.mro()}
                            - {-1},
                        )
                        != 0
                        and not inspect.isabstract(cls)
                    ):
                        builder = ArtifactServiceBuilder()
                        services.register_builder(name.lower(), builder(cls))
                        installed.append(name.lower())

    logger.debug(f"Artifacts loaded: {len(services)}")


def crunch_artifacts(
    artifact_list,
    input_path,
) -> bool:

    core_artifacts = {}
    selected_artifacts = {}

    for name, artifact in artifact_list:
        if artifact.core:
            core_artifacts.update({name: artifact})
        elif artifact.selected:
            selected_artifacts.update({name: artifact})

    if len(core_artifacts) > 0:
        for name, artifact in core_artifacts.items():
            # Now ready to run
            # Special processing for iTunesBackup Info.plist as it is a
            # separate entity, not part of the Manifest.db. Seeker won't find it
            if name == "ITunesBackupInfo":
                info_plist_path = Path(input_path) / "Info.plist"
                if info_plist_path.exists():
                    _process_artifact(name, artifact)
                else:
                    logger.info(
                        "Info.plist not found for iTunes Backup!",
                        extra={"flow": "no_filter"},
                    )
                # noqa GuiWindow.SetProgressBar(categories_searched * ratio)
            else:
                _process_artifact(name, artifact)

    if len(selected_artifacts) > 0:
        for name, artifact in selected_artifacts.items():
            _process_artifact(name, artifact)


def _process_artifact(name: str, artifact: "AbstractArtifact") -> None:
    logger.info(
        f"\n{artifact.category} [{name}] artifact " f"processing...",
        extra={"flow": "no_filter"},
    )

    artifact.process_time, _ = artifact.process()

    logger.info(
        f"{artifact.category} [{name}] artifact "
        f"finished in {artifact.process_time:.2f}s",
        extra={"flow": "no_filter"},
    )


def generate_report(name: str, artifact: "AbstractArtifact", output_folder) -> None:
    if artifact.report(output_folder):
        logger.info(
            f"\t-> {artifact.category} [{name}]",
            extra={"flow": "no_filter"},
        )


def selected(artifacts: Dict[str, object]) -> List:
    return [
        (name, artifact)
        for name, artifact in artifacts.items()
        if (artifact.selected or artifact.core)
    ]


def select(
    artifacts: List["AbstractArtifact"],
    artifact_name: str = None,
    all_artifacts: bool = False,
    long_running_process: bool = False,
    reset: bool = False,
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
    if artifact_name:
        selected = not artifacts.get(artifact_name).selected
        artifacts.get(artifact_name).selected = selected
    else:
        for _, artifact in artifacts.items():
            if reset:
                if not artifact.core:
                    artifact.selected = False
            elif all_artifacts:
                if artifact.long_running_process and not artifact.core:
                    if long_running_process:
                        artifact.selected = False
                elif not artifact.core:
                    artifact.selected = not artifact.selected


def generate_artifact_path_list(artifacts) -> None:
    """Generates path file for usage with Autopsy

    Args:
        artifacts(list): List of artifacts to get regex from.
    """
    logger.info("Artifact path list generation started.")

    with open("path_list.txt", "w") as paths:
        regex_list = []
        for artifact in artifacts:
            if isinstance(artifact.search_dirs, tuple):
                [regex_list.append(item) for item in artifact.search_dirs]
            else:
                regex_list.append(artifact.search_dirs)
        # Create a single list removing duplications
        ordered_regex_list = "\n".join(set(regex_list))
        logger.info(ordered_regex_list)
        paths.write(ordered_regex_list)

        logger.info("Artifact path list generation completed")


def generate_artifact_table(artifacts) -> None:
    """Generates artifact list table.

    Args:
        artifacts(list): List of artifacts to get regex from.
    """
    headers = ["Short Name", "Full Name", "Search Regex"]
    wrapper = TextWrapper(expand_tabs=False, replace_whitespace=False, width=60)
    output_table = prettytable.PrettyTable(headers, align="l")
    output_table.hrules = prettytable.ALL
    output_file = Path("artifact_table.txt")

    logger.info("Artifact table generation started.")

    with open(output_file, "w") as paths:
        for key, value in artifacts:
            short_name = key
            full_name = value.cls.name
            search_regex = value.cls.search_dirs
            if isinstance(search_regex, tuple):
                search_regex = "\n".join(search_regex)
            output_table.add_row([short_name, full_name, wrapper.fill(search_regex)])
        paths.write(output_table.get_string(title="Artifact List", sortby="Short Name"))
    logger.info(f"Table saved to: {output_file}", extra={"flow": "no_flter"})
    logger.info("Artifact table generation completed", extra={"flow": "no_filter"})


services: "ArtifactService" = ArtifactService()
installed: List["AbstractArtifact"] = []

_build_artifact_list()
