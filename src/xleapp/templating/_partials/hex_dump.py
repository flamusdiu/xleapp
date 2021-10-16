import binascii
import math
from dataclasses import dataclass

import xleapp.helpers.strings as istrings
from xleapp.templating._html import HtmlPage, Template


@dataclass
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
