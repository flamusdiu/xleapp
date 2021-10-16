import os
import re
import typing as t
from pathlib import Path

from xleapp import __authors__


class ParseError(Exception):
    pass


def is_platform_windows() -> bool:
    """Returns True if running on Windows"""
    return os.name == "nt"


def sanitize_file_path(filename: str, replacement_char: str = "_") -> str:
    """
    Removes illegal characters (for windows) from the string passed.
    Does not replace \\ or /
    """
    return re.sub(r'[*?:"<>|\'\r\n]', replacement_char, filename)


def sanitize_file_name(filename: str, replacement_char: str = "_") -> str:
    """
    Removes illegal characters (for windows) from the string passed.
    """
    return re.sub(r'[\\/*?:"<>|\'\r\n]', replacement_char, filename)


def get_next_unused_name(path: str) -> str:
    """Checks if path exists, if it does, finds an unused name by appending -xx
    where xx=00-99. Return value is new path.
    If it is a file like abc.txt, then abc-01.txt will be the next
    """
    folder, basename = os.path.split(path)
    ext = None
    if basename.find(".") > 0:
        basename, ext = os.path.splitext(basename)
    num = 1
    new_name = basename
    if ext is None:
        new_name += f"{ext}"
    while os.path.exists(os.path.join(folder, new_name)):
        new_name = basename + "-{:02}".format(num)
        if ext is None:
            new_name += f"{ext}"
        num += 1
    return os.path.join(folder, new_name)


def ValidateInput(
    input_path: str,
    output_path: str,
    selected_artifacts: list,
) -> t.Union[str, str]:
    """
    Returns tuple (success, extraction_type)
    """

    if input_path is None:
        raise ParseError("No INPUT file or folder selected!")
    else:
        i_path = Path(input_path)  # input file/folder
        if not i_path.exists():
            raise ParseError("INPUT file/folder does not exist!")

    if output_path is None:
        raise ParseError("No OUTPUT folder selected!")
    else:
        o_path = Path(output_path)  # output folder
        if not o_path.exists():
            raise ParseError("OUTPUT does not exist!")

    if len(selected_artifacts) == 0:
        raise ParseError("No module selected for processing!")
    elif i_path.is_dir() and (i_path / "Manifest.db").exists():
        ext_type = "itunes"
    elif i_path.is_dir():
        ext_type = "fs"
    else:  # must be an existing file then
        ext_type = i_path.suffix[1:].lower()
        if ext_type not in ["tar", "zip", "gz"]:
            raise ParseError(f"Input file is not a supported archive! \n {i_path}")

    return ext_type


def generate_program_header(
    project_version: str,
    input_path: Path,
    output_path: Path,
    num_to_process: int,
    num_of_categories: int,
):
    project, version = project_version.split(" ")
    header = (
        "Procesing started. Please wait. This may take a "
        "few minutes...\n"
        "-----------------------------------------------------------"
        "---------------------------\n\n"
        f"{project} {version}: xLEAPP Logs, "
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


def filter_dict(d: dict, filter_string: str):
    for key, val in d.items():
        if filter_string not in key:
            continue
        yield key, val
