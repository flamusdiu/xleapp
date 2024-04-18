import abc
from dataclasses import dataclass
from typing import Sized

from .base import MagicType


@dataclass
class ZippedDocumentBase(abc.ABC, MagicType):
    def match(self, buf: bytes) -> bool:
        # start by checking for ZIP local file header signature
        if self.search_signature(buf, 0, 6000) != 0:
            return False

        return self.match_document(buf)

    def match_document(self, buf: bytes) -> bool:
        raise NotImplementedError

    def compare_bytes(self, buf: bytes, subslice: Sized, start_offset: int) -> bool:
        sl = len(subslice)

        if start_offset + sl > len(buf):
            return False

        return buf[start_offset : start_offset + sl] == subslice

    def search_signature(self, buf: bytes, start: int, rangeNum: int) -> int:
        signature = b"PK\x03\x04"
        length = len(buf)

        end = start + rangeNum
        end = length if end > length else end

        if start >= end:
            return -1

        try:
            return buf.index(signature, start, end)
        except ValueError:
            return -1


@dataclass
class OpenDocument(ZippedDocumentBase):
    def match_document(self, buf: bytes) -> bool:
        # Check if first file in archive is the identifying file
        if not self.compare_bytes(buf, b"mimetype", 0x1E):
            return False

        # Check content of mimetype file if it matches current mime
        return self.compare_bytes(buf, bytes(self.MIME, "ASCII"), 0x26)


@dataclass
class OfficeOpenXml(ZippedDocumentBase):
    def match_document(self, buf: bytes) -> bool:
        # Check if first file in archive is the identifying file
        if ft := self.match_filename(buf, 0x1E):
            return ft

        # Otherwise check that the fist file is one of these
        if (
            not self.compare_bytes(buf, b"[Content_Types].xml", 0x1E)
            and not self.compare_bytes(buf, b"_rels/.rels", 0x1E)
            and not self.compare_bytes(buf, b"docProps", 0x1E)
        ):
            return False

        # Loop through next 3 files and check if they match
        # NOTE: OpenOffice/Libreoffice orders ZIP entry differently, so check the 4th file
        # https://github.com/h2non/filetype/blob/d730d98ad5c990883148485b6fd5adbdd378364a/matchers/document.go#L134
        idx = 0
        for _ in range(4):
            # Search for next file header
            if idx := self.search_signature(buf, idx + 4, 6000) == -1:
                return False

            # Filename is at file header + 30
            if ft := self.match_filename(buf, idx + 30):
                return ft
        return False

    def match_filename(self, buf: bytes, offset: int) -> bool:
        if self.compare_bytes(buf, b"word/", offset):
            return (
                self.MIME
                == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        if self.compare_bytes(buf, b"ppt/", offset):
            return (
                self.MIME
                == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            )
        if self.compare_bytes(buf, b"xl/", offset):
            return (
                self.MIME
                == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        return False


@dataclass
class Doc(MagicType):
    """
    Implements the Microsoft Word (Office 97-2003) document type matcher.
    """

    MIME = "application/msword"
    EXTENSION: str = "doc"

    def match(self, buf: bytes) -> bool:
        if len(buf) > 515 and buf[0:8] == b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1":
            if buf[512:516] == b"\xEC\xA5\xC1\x00":
                return True
            if len(buf) > 2142 and (
                b"\x00\x0A\x00\x00\x00MSWordDoc\x00\x10\x00\x00\x00Word.Document.8\x00\xF49\xB2q"
                in buf[2075:2142]
                or b"W\0o\0r\0d\0D\0o\0c\0u\0m\0e\0n\0t\0" in buf[0x580:0x598]
            ):
                return True

        return False


class Docx(OfficeOpenXml):
    """
    Implements the Microsoft Word OOXML (Office 2007+) document type matcher.
    """

    MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    EXTENSION: str = "docx"


class Odt(OpenDocument):
    """
    Implements the OpenDocument Text document type matcher.
    """

    MIME = "application/vnd.oasis.opendocument.text"
    EXTENSION: str = "odt"


@dataclass
class Xls(MagicType):
    """
    Implements the Microsoft Excel (Office 97-2003) document type matcher.
    """

    MIME = "application/vnd.ms-excel"
    EXTENSION: str = "xls"

    def match(self, buf: bytes) -> bool:
        if len(buf) > 520 and buf[0:8] == b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1":
            if buf[512:516] == b"\xFD\xFF\xFF\xFF" and (
                buf[518] == 0x00 or buf[518] == 0x02
            ):
                return True
            if buf[512:520] == b"\x09\x08\x10\x00\x00\x06\x05\x00":
                return True
            if (
                len(buf) > 2095
                and b"\xE2\x00\x00\x00\x5C\x00\x70\x00\x04\x00\x00Calc" in buf[1568:2095]
            ):
                return True

        return False


class Xlsx(OfficeOpenXml):
    """
    Implements the Microsoft Excel OOXML (Office 2007+) document type matcher.
    """

    MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    EXTENSION: str = "xlsx"


class Ods(OpenDocument):
    """
    Implements the OpenDocument Spreadsheet document type matcher.
    """

    MIME = "application/vnd.oasis.opendocument.spreadsheet"
    EXTENSION: str = "ods"


@dataclass
class Ppt(MagicType):
    """
    Implements the Microsoft PowerPoint (Office 97-2003) document type matcher.
    """

    MIME = "application/vnd.ms-powerpoint"
    EXTENSION: str = "ppt"

    def match(self, buf: bytes) -> bool:
        if len(buf) > 524 and buf[0:8] == b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1":
            if buf[512:516] == b"\xA0\x46\x1D\xF0":
                return True
            if buf[512:516] == b"\x00\x6E\x1E\xF0":
                return True
            if buf[512:516] == b"\x0F\x00\xE8\x03":
                return True
            if buf[512:516] == b"\xFD\xFF\xFF\xFF" and buf[522:524] == b"\x00\x00":
                return True
            if (
                len(buf) > 2096
                and buf[2072:2096] == b"\x00\xB9\x29\xE8\x11\x00\x00\x00MS PowerPoint 97"
            ):
                return True

        return False


class Pptx(OfficeOpenXml):
    """
    Implements the Microsoft PowerPoint OOXML (Office 2007+) document type matcher.
    """

    MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    EXTENSION: str = "pptx"


class Odp(OpenDocument):
    """
    Implements the OpenDocument Presentation document type matcher.
    """

    MIME = "application/vnd.oasis.opendocument.presentation"
    EXTENSION: str = "odp"
