import logging
import shutil
import typing as t

from os import PathLike
from pathlib import Path
from textwrap import TextWrapper

import prettytable

import xleapp.helpers.utils as utils

from ._abstract import Artifact
from ._decorators import Search, core_artifact, long_running_process


if t.TYPE_CHECKING:
    from xleapp.app import XLEAPP

logger_log = logging.getLogger("xleapp.logfile")


def crunch_artifacts(app: "XLEAPP") -> None:
    def process(artifacts):
        for artifact in artifacts:
            if not artifact.select:
                continue
            # Now ready to run
            # Special processing for iTunesBackup Info.plist as it is a
            # separate entity, not part of the Manifest.db. Seeker won't find it
            if artifact.cls_name == "ITunesBackupInfo":
                info_plist_path = Path(app.input_path) / "Info.plist"
                if info_plist_path.exists():
                    app.artifacts["ITunesBackupInfo"].process()
                else:
                    logger_log.info("Info.plist not found for iTunes Backup!")
                # noqa GuiWindow.SetProgressBar(categories_searched * ratio)
            else:
                artifact.process()

    # Process core artifacts first
    core = filter(
        lambda artifact: artifact.core and artifact.select,
        app.artifacts,
    )
    process(core)

    # Process everything else
    standard = filter(
        lambda artifact: not artifact.core and artifact.select,
        app.artifacts,
    )
    process(standard)


def generate_artifact_path_list(artifacts) -> None:
    """Generates path file for usage with Autopsy

    Args:
        artifacts(list): List of artifacts to get regex from.
    """
    logger_log.info("Artifact path list generation started.")

    with open("path_list.txt", "w") as paths:
        regex_list = []
        for artifact in artifacts:
            if isinstance(artifact.search_dirs, tuple):
                [regex_list.append(item) for item in artifact.search_dirs]
            else:
                regex_list.append(artifact.search_dirs)
        # Create a single list removing duplications
        ordered_regex_list = "\n".join(set(regex_list))
        logger_log.info(ordered_regex_list)
        paths.write(ordered_regex_list)

        logger_log.info("Artifact path list generation completed")


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

    logger_log.info("Artifact table generation started.")

    with open(output_file, "w") as paths:
        for key, value in artifacts:
            short_name = key
            full_name = value.cls.name
            search_regex = value.cls.search_dirs
            if isinstance(search_regex, tuple):
                search_regex = "\n".join(search_regex)
            output_table.add_row([short_name, full_name, wrapper.fill(search_regex)])
        paths.write(output_table.get_string(title="Artifact List", sortby="Short Name"))
    logger_log.info(f"Table saved to: {output_file}")
    logger_log.info("Artifact table generation completed")


def copyfile(
    report_folder: Path,
    name: str,
    input_file: t.Union[PathLike, str],
    output_file: str,
) -> Path:
    """Exports file to report folder

    File will be located under report_folder\\export\\artifact_class

    Args:
        names(str): name of the artifact class
        input_file (str): input file name/path
        output_file (str): output file name

    Returns:
        output_file (Path): Path object of the file save location and name.
    """
    report_folder = report_folder
    artifact_folder = name
    output_folder = Path(report_folder / "export" / artifact_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    if utils.is_platform_windows():
        input_file = Path(f"\\\\?\\{input_file.resolve()}")

    output_file = Path(output_folder / output_file)
    shutil.copy2(input_file, output_file)
    logger_log.debug(f"File {input_file.name} copied to " f"{output_file}")
    return output_file


def filter_artifacts(artifact_list: t.Iterable) -> filter:
    return filter(
        lambda artifact: getattr(artifact, "select", False) is True,
        artifact_list,
    )
