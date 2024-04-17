import binascii
import math

from dataclasses import dataclass

import xleapp.helpers.strings as is_strings

from xleapp import templating


@dataclass
class HexDumpHtml(templating.HtmlPage):
    @templating.Template("hexdump")
    def html(self, data, char_per_row=5) -> str:
        """Retuns HTML table of the hexdump of the passed in data."""
        data_hex = binascii.hexlify(data).decode("utf-8")
        str_raw = is_strings.raw(data)
        str_hex = ""
        str_ascii = ""

        # Generates offset column
        offset_rows = math.ceil(len(data_hex) / (char_per_row * 2))
        offsets = [range(0, len(data_hex), char_per_row)][:offset_rows]
        str_offset = "<br>".join([str(hex(s)[2:]).zfill(4).upper() for s in offsets])

        # Generates hex data column
        char = 0
        for i in range(0, len(data_hex), 2):
            str_hex += data_hex[i : i + 2] + "&nbsp;"

            if char == char_per_row - 1:
                str_hex += "<br>"
                char = 0
            else:
                char += 1

        # Generates ascii column of data
        for i in range(0, len(str_raw), char_per_row):
            str_ascii += str_raw[i : i + char_per_row] + "<br>"

        return self.template.render(str_offset, str_hex, str_ascii)
