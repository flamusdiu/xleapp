import os
import re
import typing as t

from collections import defaultdict
from datetime import datetime
from functools import reduce
from importlib.metadata import entry_points
from pathlib import Path

from xleapp import __authors__
from xleapp.plugins import Plugin


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


def validate_input(input_path: str, output_path: str) -> None:
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


def filter_dict(dictionary: dict, filter_string: str):
    for key, item in dictionary.items():
        if filter_string not in key:
            continue
        yield key, item


class PluginMissingError(RuntimeError):
    """Raised when no modules are installed!"""

    pass


def discovered_plugins() -> t.Optional[dict[str, set[Plugin]]]:
    plugins: dict[str, set[Plugin]] = defaultdict(set)
    try:
        for plugin in entry_points()["xleapp.plugins"]:
            xleapp_plugin: Plugin = plugin.load()()
            plugins[plugin.name].add(xleapp_plugin)
        return plugins
    except KeyError:
        raise PluginMissingError("No plugins installed! Exiting!")


def unix_epoch_to_readable_date(unix_epoch_time: int):
    unix_time = float(unix_epoch_time + 978307200)
    readable_time = datetime.utcfromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S")
    return readable_time


def is_list(value) -> bool:
    return isinstance(value, list)


def deep_get(dictionary: dict, *keys: str) -> t.Any:
    """Searches dictionary for keys

    Args:
        dictionary: dictionary to search
        keys: strings as keys

    Returns:
        Returns value of the key
    """
    return reduce(
        lambda d, key: d.get(key, "") if isinstance(d, dict) else "",
        keys,
        dictionary,
    )


def filter_json(self, json: t.Any, fields: tuple[str | tuple[str]]) -> dict:
    """Returns a dictionary from a json object

    Args:
        json: JSON object to search
        fields: Fields to filter JSON object by

    Returns:
        Returns dictonary of filtered data
    """
    json_dict = {}
    for field in fields:
        if isinstance(field, tuple):
            json_value = deep_get(json, *field)
        else:
            json_value = json.get(field, "")
        json_dict.update({field: json_value})
    return json_dict


def time_factor_conversion(time_in_utc: str) -> str:
    # time_in_utc has to be a string
    if len(time_in_utc) == 16:
        time_factor = 1000000
    else:
        time_factor = 1000
    time_in_utc = int(time_in_utc)
    if time_in_utc > 0:
        time_in_utc = datetime.fromtimestamp(time_in_utc / time_factor)
        time_in_utc = str(time_in_utc)
    return time_in_utc
