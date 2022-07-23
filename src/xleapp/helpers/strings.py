import re
import string
import typing as t

from pathlib import Path


def raw(data: t.ByteString) -> str:
    """Returns string of printable characters. Replacing non-printable characters
    with '.', or CHR(46)
    ``"""
    return "".join(
        [chr(byte) if byte >= 0x20 and byte < 0x7F else chr(46) for byte in data],
    )


def print_str(data: t.ByteString) -> filter:
    """Returns string of printable characters. Works similar to the Linux
    `string` function.
    """
    cleansed = "".join(
        [chr(byte) if byte >= 0x20 and byte < 0x7F else chr(0) for byte in data],
    )
    return filter(lambda string: len(string) >= 4, cleansed.split(chr(0)))


def split_camel_case(value: str) -> list[str]:
    return re.sub("([A-Z][a-z]+)", r" \1", re.sub("([A-Z]+)", r" \1", value)).split()


def wrap_text(
    source_text: str,
    separator_chars: str,
    width: int = 70,
    keep_separators: bool = True,
):
    current_length = 0
    latest_separator = -1
    current_chunk_start = 0
    output = ""
    char_index = 0
    while char_index < len(source_text):
        if source_text[char_index] in separator_chars:
            latest_separator = char_index
        output += source_text[char_index]
        current_length += 1
        if current_length == width:
            if latest_separator >= current_chunk_start:
                # Valid earlier separator, cut there
                cutting_length = char_index - latest_separator
                if not keep_separators:
                    cutting_length += 1
                if cutting_length:
                    output = output[:-cutting_length]
                output += "\n"
                current_chunk_start = latest_separator + 1
                char_index = current_chunk_start
            else:
                # No separator found, hard cut
                output += "\n"
                current_chunk_start = char_index + 1
                latest_separator = current_chunk_start - 1
                char_index += 1
            current_length = 0
        else:
            char_index += 1
    return output


def filter_strings_in_file(filename: Path, min_chars=4):
    with open(filename, errors="ignore") as file:
        result = ""
        printable = set(string.printable)
        for char in file.read():
            if char in printable:
                result += char
                continue
            if len(result) >= min_chars:
                yield result
            result = ""
        if len(result) >= min_chars:  # catch reslt at EOF
            yield result
