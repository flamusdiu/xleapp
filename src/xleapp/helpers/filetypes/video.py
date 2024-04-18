from .base import MagicType
from .isobmff import IsoBmff


class Mp4(IsoBmff):
    """
    Implements the MP4 video type matcher.
    """

    MIME: str = "video/mp4"
    EXTENSION: str = "mp4"

    def match(self, buf: bytes) -> bool:
        if not self._is_isobmff(buf):
            return False

        major_brand, minor_version, compatible_brands = self._get_ftyp(buf)
        for brand in compatible_brands:
            if brand in ["mp41", "mp42", "isom"]:
                return True
        return major_brand in ["mp41", "mp42", "isom"]


class M4v(MagicType):
    """
    Implements the M4V video type matcher.
    """

    MIME: str = "video/x-m4v"
    EXTENSION: str = "m4v"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 10
            and buf[0] == 0x0
            and buf[1] == 0x0
            and buf[2] == 0x0
            and buf[3] == 0x1C
            and buf[4] == 0x66
            and buf[5] == 0x74
            and buf[6] == 0x79
            and buf[7] == 0x70
            and buf[8] == 0x4D
            and buf[9] == 0x34
            and buf[10] == 0x56
        )


class Mkv(MagicType):
    """
    Implements the MKV video type matcher.
    """

    MIME: str = "video/x-matroska"
    EXTENSION: str = "mkv"

    def match(self, buf: bytes) -> bool:
        contains_ebml_element = buf.startswith(b"\x1A\x45\xDF\xA3")
        contains_doctype_element = buf.find(b"\x42\x82\x88matroska") > -1
        return contains_ebml_element and contains_doctype_element


class Webm(MagicType):
    """
    Implements the WebM video type matcher.
    """

    MIME: str = "video/webm"
    EXTENSION: str = "webm"

    def match(self, buf: bytes) -> bool:
        contains_ebml_element = buf.startswith(b"\x1A\x45\xDF\xA3")
        contains_doctype_element = buf.find(b"\x42\x82\x84webm") > -1
        return contains_ebml_element and contains_doctype_element


class Mov(IsoBmff):
    """
    Implements the MOV video type matcher.
    """

    MIME: str = "video/quicktime"
    EXTENSION: str = "mov"

    def match(self, buf: bytes) -> bool:
        if not self._is_isobmff(buf):
            return False

        major_brand, minor_version, compatible_brands = self._get_ftyp(buf)
        return major_brand == "qt  "


class Avi(MagicType):
    """
    Implements the AVI video type matcher.
    """

    MIME: str = "video/x-msvideo"
    EXTENSION: str = "avi"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 11
            and buf[0] == 0x52
            and buf[1] == 0x49
            and buf[2] == 0x46
            and buf[3] == 0x46
            and buf[8] == 0x41
            and buf[9] == 0x56
            and buf[10] == 0x49
            and buf[11] == 0x20
        )


class Wmv(MagicType):
    """
    Implements the WMV video type matcher.
    """

    MIME: str = "video/x-ms-wmv"
    EXTENSION: str = "wmv"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 9
            and buf[0] == 0x30
            and buf[1] == 0x26
            and buf[2] == 0xB2
            and buf[3] == 0x75
            and buf[4] == 0x8E
            and buf[5] == 0x66
            and buf[6] == 0xCF
            and buf[7] == 0x11
            and buf[8] == 0xA6
            and buf[9] == 0xD9
        )


class Flv(MagicType):
    """
    Implements the FLV video type matcher.
    """

    MIME: str = "video/x-flv"
    EXTENSION: str = "flv"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 3
            and buf[0] == 0x46
            and buf[1] == 0x4C
            and buf[2] == 0x56
            and buf[3] == 0x01
        )


class Mpeg(MagicType):
    """
    Implements the MPEG video type matcher.
    """

    MIME: str = "video/mpeg"
    EXTENSION: str = "mpg"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 3
            and buf[0] == 0x0
            and buf[1] == 0x0
            and buf[2] == 0x1
            and buf[3] >= 0xB0
            and buf[3] <= 0xBF
        )


class M3gp(MagicType):
    """Implements the 3gp video type matcher."""

    MIME: str = "video/3gpp"
    EXTENSION: str = "3gp"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 10
            and buf[4] == 0x66
            and buf[5] == 0x74
            and buf[6] == 0x79
            and buf[7] == 0x70
            and buf[8] == 0x33
            and buf[9] == 0x67
            and buf[10] == 0x70
        )
