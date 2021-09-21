import datetime
import logging
from collections import UserDict
from pathlib import Path
from typing import Type, Union

from ileapp._authors import __authors__
from ileapp._version import VERSION as __version__  # noqa N811
from ileapp.helpers.search import FileSeekerBase

logger = logging.getLogger(__name__)

THUMBNAIL_ROOT = "**/Media/PhotoData/Thumbnails/**"
MEDIA_ROOT = "**/Media"
THUMB_SIZE = 256, 256


class Device(UserDict):
    def table(self):
        return [[key, value] for key, value in self.data.items()]


def set_output_folder(output_folder) -> tuple:
    """Sets and creates output folders for the reports

    Args:
        output_folder (str or Path): output folder for reports

    Returns:
        tuple: folder paths for report, temp, and log folders
    """
    now = datetime.datetime.now()
    current_time = now.strftime("%Y-%m-%d_%A_%H%M%S")

    report_folder = Path(output_folder) / f"iLEAPP_Reports_{current_time}"

    temp_folder = report_folder / "temp"
    log_folder = report_folder / "Script Logs"
    log_folder.mkdir(parents=True, exist_ok=True)
    temp_folder.mkdir(parents=True, exist_ok=True)
    return report_folder, temp_folder, log_folder


def generate_program_header(input_path, output_path, num_to_process, num_of_categories):
    project, version = __version__.split(" ")
    header = (
        "Procesing started. Please wait. This may take a "
        "few minutes...\n"
        "-----------------------------------------------------------"
        "---------------------------\n\n"
        f"{project} {version}: iLEAPP Logs, "
        "Events, and Properties Parser\n"
        "Objective: Triage iOS Full System Extractions.\n\n"
    )

    for author in __authors__:
        header += f"By: {author[0]} | {author[2]} | {author[1]}\n"

    header += (
        f"\nArtifacts to parse: {num_to_process} in {num_of_categories} "
        "categories\n"
        f"File/Path Selected: {input_path}\n"
        f"Output: {output_path}\n\n"
        "-----------------------------------------------------------"
        "---------------------------\n"
    )
    return header


# Global Class
device = Device()

# Global search object
seeker = Type[FileSeekerBase]

# Report Folder Base
report_folder = Union[Type[str], Type[Path]]
