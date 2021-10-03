import binascii
import importlib
import inspect
import logging
import math
import os
import re
from pathlib import Path
from typing import Union

import xleapp.helpers.strings as istrings
from xleapp.report.templating import HtmlPage, Template

logger = logging.getLogger(__name__)


def is_platform_windows():
    """Returns True if running on Windows"""
    return os.name == "nt"


def sanitize_file_path(filename, replacement_char="_"):
    """
    Removes illegal characters (for windows) from the string passed.
    Does not replace \\ or /
    """
    return re.sub(r'[*?:"<>|\'\r\n]', replacement_char, filename)


def sanitize_file_name(filename, replacement_char="_"):
    """
    Removes illegal characters (for windows) from the string passed.
    """
    return re.sub(r'[\\/*?:"<>|\'\r\n]', replacement_char, filename)


def get_next_unused_name(path):
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


class HexDumpHtml(HtmlPage):
    @Template("hexdump")
    def html(self, data, char_per_row=5):
        """Retuns HTML table of the hexdump of the passed in data."""
        data_hex = binascii.hexlify(data).decode("utf-8")
        str_raw = istrings.strings_raw(data)
        str_hex = ""
        str_ascii = ""

        """ Generates offset column
        """
        offset_rows = math.ceil(len(data_hex) / (char_per_row * 2))
        offsets = [i for i in range(0, len(data_hex), char_per_row)][:offset_rows]
        str_offset = "<br>".join([str(hex(s)[2:]).zfill(4).upper() for s in offsets])

        """ Generates hex data column
        """
        c = 0
        for i in range(0, len(data_hex), 2):
            str_hex += data_hex[i : i + 2] + "&nbsp;"

            if c == char_per_row - 1:
                str_hex += "<br>"
                c = 0
            else:
                c += 1

        """ Generates ascii column of data
        """
        for i in range(0, len(str_raw), char_per_row):
            str_ascii += str_raw[i : i + char_per_row] + "<br>"

        return self.template.render(str_offset, str_hex, str_ascii)
        """
        return f"
        <table id="GeoLocationHexTable" aria-describedby="GeoLocationHexTable" cellspacing="0">
        <thead>
            <tr>
            <th style="border-right: 1px solid #000;border-bottom: 1px solid #000;">Offset</th>
            <th style="width: 100px; border-right: 1px solid #000;border-bottom: 1px solid #000;">Hex</th>
            <th style="border-bottom: 1px solid #000;">Ascii</th>
        </tr>
        </thead>
        <tbody>
        <tr>
        <td style="white-space:nowrap; border-right: 1px solid #000;">{str_offset}</td>
        <td style="border-right: 1px solid #000; white-space:nowrap;">{str_hex}</td>
        <td style="white-space:nowrap;">{str_ascii}</td>
        </tr></tbody></table>
        "
        """


def ValidateInput(
    input_path: str,
    output_path: str,
    selected_artifacts: list,
) -> Union[str, str]:
    """
    Returns tuple (success, extraction_type)
    """

    if input_path is None:
        return None, "No INPUT file or folder selected!"
    else:
        i_path = Path(input_path)  # input file/folder
        if not i_path.exists():
            return None, "INPUT file/folder does not exist!"

    if output_path is None:
        return None, "No OUTPUT folder selected!"
    else:
        o_path = Path(output_path)  # output folder
        if not o_path.exists():
            return None, "OUTPUT does not exist!"

    if len(selected_artifacts) == 0:
        return None, "No module selected for processing!"
    elif i_path.is_dir() and (i_path / "Manifest.db").exists():
        ext_type = "itunes"
    elif i_path.is_dir():
        ext_type = "fs"
    else:  # must be an existing file then
        ext_type = i_path.suffix[1:].lower()
        if ext_type not in ["tar", "zip", "gz"]:
            return None, f"Input file is not a supported archive! \n {i_path}"

    return ext_type, ""
