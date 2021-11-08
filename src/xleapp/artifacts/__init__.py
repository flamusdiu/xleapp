import logging
import shutil
import typing as t

from pathlib import Path
from textwrap import TextWrapper

import prettytable

import xleapp.helpers.utils as utils

from .abstract import Artifact as Artifact
from .decorators import Search as Search
from .decorators import core_artifact as core_artifact
from .decorators import long_running_process as long_running_process
from .services import ArtifactEnum as ArtifactEnum
from .services import ArtifactError as ArtifactError
from .services import Artifacts as Artifacts


logger_log = logging.getLogger("xleapp.logfile")


def generate_artifact_path_list(artifacts: Artifacts) -> None:
    """Generates path file for usage with Autopsy

    Args:
        artifacts: List of artifacts to get regex from.
    """
    logger_log.info("Artifact path list generation started.")

    with open("path_list.txt", "w") as paths:
        regex_list: set[str] = set()
        for artifact in artifacts.data:
            regex_list = regex_list | artifact.regex
        # Create a single list removing duplications
        ordered_regex_list = "\n".join(regex_list)
        logger_log.info(ordered_regex_list)
        paths.write(ordered_regex_list)

        logger_log.info("Artifact path list generation completed")


def generate_artifact_table(artifacts: Artifacts) -> None:
    """Generates artifact list table.

    Args:
        artifacts: List of artifacts to get regex from.
    """
    headers = ["Short Name", "Full Name", "Search Regex"]
    wrapper = TextWrapper(expand_tabs=False, replace_whitespace=False, width=60)
    output_table = prettytable.PrettyTable(headers, align="l")
    output_table.hrules = prettytable.ALL
    output_file = Path("artifact_table.txt")

    logger_log.info("Artifact table generation started.")

    with open(output_file, "w") as paths:
        for artifact in artifacts.data:
            short_name: str = artifact.cls_name
            full_name: str = artifact.value.name
            search_regex: set[str] = artifact.regex
            search_regex_list = "\n".join(search_regex)
            output_table.add_row([short_name, full_name, wrapper.fill(search_regex_list)])
        paths.write(output_table.get_string(title="Artifact List", sortby="Short Name"))
    logger_log.info(f"Table saved to: {output_file}")
    logger_log.info("Artifact table generation completed")


def copyfile(
    input_file: Path,
    output_file: Path,
) -> Path:
    """Exports file to report folder

    File will be located under report_folder\\export\\artifact_class

    Args:
        input_file: input file name/path
        output_file: output file name

    Returns:
        output_file: Path object of the file save location and name.
    """
    if input_file.is_file():
        output_file.parent.mkdir(parents=True, exist_ok=True)
    else:
        output_file.mkdir(parents=True, exist_ok=True)

    if utils.is_platform_windows():
        input_file = Path(f"\\\\?\\{input_file.resolve()}")

    shutil.copy2(input_file, output_file)
    logger_log.debug(f"File {input_file.name} copied to " f"{output_file}")
    return output_file


def filter_artifacts(artifact_list: t.Iterable) -> filter:
    return filter(
        lambda artifact: getattr(artifact, "select", False) is True,
        artifact_list,
    )
