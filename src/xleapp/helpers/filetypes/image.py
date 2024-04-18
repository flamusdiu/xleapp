from dataclasses import dataclass

from .base import MagicType
from .isobmff import IsoBmff


@dataclass
class Jpeg(MagicType):
    """
    Implements the JPEG image type matcher.
    """

    MIME: str = "image/jpeg"
    EXTENSION: str = "jpg"

    def match(self, buf: bytes) -> bool:
        return len(buf) > 2 and buf[0] == 0xFF and buf[1] == 0xD8 and buf[2] == 0xFF


@dataclass
class Jpx(MagicType):
    """
    Implements the JPEG2000 image type matcher.
    """

    MIME: str = "image/jpx"
    EXTENSION: str = "jpx"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 50
            and buf[0] == 0x00
            and buf[1] == 0x00
            and buf[2] == 0x00
            and buf[3] == 0x0C
            and buf[16:24] == b"ftypjp2 "
        )


@dataclass
class Apng(MagicType):
    """
    Implements the APNG image type matcher.
    """

    MIME: str = "image/apng"
    EXTENSION: str = "apng"

    def match(self, buf: bytes) -> bool:
        if len(buf) > 8 and buf[:8] == bytearray(
            [0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]
        ):
            # cursor in buf, skip already readed 8 bytes
            i = 8
            while len(buf) > i:
                data_length = int.from_bytes(buf[i : i + 4], byteorder="big")
                i += 4

                chunk_type = buf[i : i + 4].decode("ascii", errors="ignore")
                i += 4

                # acTL chunk in APNG must appear before IDAT
                # IEND is end of PNG
                if chunk_type == "IDAT" or chunk_type == "IEND":
                    return False
                if chunk_type == "acTL":
                    return True

                # move to the next chunk by skipping data and crc (4 bytes)
                i += data_length + 4

        return False


@dataclass
class Png(MagicType):
    """
    Implements the PNG image type matcher.
    """

    MIME: str = "image/png"
    EXTENSION: str = "png"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 3
            and buf[0] == 0x89
            and buf[1] == 0x50
            and buf[2] == 0x4E
            and buf[3] == 0x47
        )


@dataclass
class Gif(MagicType):
    """
    Implements the GIF image type matcher.
    """

    MIME: str = "image/gif"
    EXTENSION: str = "gif"

    def match(self, buf: bytes) -> bool:
        return len(buf) > 2 and buf[0] == 0x47 and buf[1] == 0x49 and buf[2] == 0x46


@dataclass
class Webp(MagicType):
    """
    Implements the WEBP image type matcher.
    """

    MIME: str = "image/webp"
    EXTENSION: str = "webp"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 13
            and buf[0] == 0x52
            and buf[1] == 0x49
            and buf[2] == 0x46
            and buf[3] == 0x46
            and buf[8] == 0x57
            and buf[9] == 0x45
            and buf[10] == 0x42
            and buf[11] == 0x50
            and buf[12] == 0x56
            and buf[13] == 0x50
        )


@dataclass
class Cr2(MagicType):
    """
    Implements the CR2 image type matcher.
    """

    MIME: str = "image/x-canon-cr2"
    EXTENSION: str = "cr2"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 9
            and (
                (buf[0] == 0x49 and buf[1] == 0x49 and buf[2] == 0x2A and buf[3] == 0x0)
                or (
                    buf[0] == 0x4D and buf[1] == 0x4D and buf[2] == 0x0 and buf[3] == 0x2A
                )
            )
            and buf[8] == 0x43
            and buf[9] == 0x52
        )


@dataclass
class Tiff(MagicType):
    """
    Implements the TIFF image type matcher.
    """

    MIME: str = "image/tiff"
    EXTENSION: str = "tif"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 9
            and (
                (buf[0] == 0x49 and buf[1] == 0x49 and buf[2] == 0x2A and buf[3] == 0x0)
                or (
                    buf[0] == 0x4D and buf[1] == 0x4D and buf[2] == 0x0 and buf[3] == 0x2A
                )
            )
            and not (buf[8] == 0x43 and buf[9] == 0x52)
        )


@dataclass
class Bmp(MagicType):
    """
    Implements the BMP image type matcher.
    """

    MIME: str = "image/bmp"
    EXTENSION: str = "bmp"

    def match(self, buf: bytes) -> bool:
        return len(buf) > 1 and buf[0] == 0x42 and buf[1] == 0x4D


@dataclass
class Jxr(MagicType):
    """
    Implements the JXR image type matcher.
    """

    MIME: str = "image/vnd.ms-photo"
    EXTENSION: str = "jxr"

    def match(self, buf: bytes) -> bool:
        return len(buf) > 2 and buf[0] == 0x49 and buf[1] == 0x49 and buf[2] == 0xBC


@dataclass
class Psd(MagicType):
    """
    Implements the PSD image type matcher.
    """

    MIME: str = "image/vnd.adobe.photoshop"
    EXTENSION: str = "psd"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 3
            and buf[0] == 0x38
            and buf[1] == 0x42
            and buf[2] == 0x50
            and buf[3] == 0x53
        )


@dataclass
class Ico(MagicType):
    """
    Implements the ICO image type matcher.
    """

    MIME: str = "image/x-icon"
    EXTENSION: str = "ico"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 3
            and buf[0] == 0x00
            and buf[1] == 0x00
            and buf[2] == 0x01
            and buf[3] == 0x00
        )


class Heic(IsoBmff):
    """
    Implements the HEIC image type matcher.
    """

    MIME: str = "image/heic"
    EXTENSION: str = "heic"

    def match(self, buf: bytes) -> bool:
        if not self._is_isobmff(buf):
            return False

        major_brand, minor_version, compatible_brands = self._get_ftyp(buf)
        if major_brand == "heic":
            return True
        if major_brand in ["mif1", "msf1"] and "heic" in compatible_brands:
            return True
        return False


@dataclass
class Dcm(MagicType):

    MIME: str = "application/dicom"
    EXTENSION: str = "dcm"
    OFFSET = 128

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > Dcm.OFFSET + 4
            and buf[Dcm.OFFSET + 0] == 0x44
            and buf[Dcm.OFFSET + 1] == 0x49
            and buf[Dcm.OFFSET + 2] == 0x43
            and buf[Dcm.OFFSET + 3] == 0x4D
        )


@dataclass
class Dwg(MagicType):
    """Implements the Dwg image type matcher."""

    MIME: str = "image/vnd.dwg"
    EXTENSION: str = "dwg"

    def match(self, buf: bytes) -> bool:
        return buf[:4] == bytearray([0x41, 0x43, 0x31, 0x30])


@dataclass
class Xcf(MagicType):
    """Implements the Xcf image type matcher."""

    MIME: str = "image/x-xcf"
    EXTENSION: str = "xcf"

    def match(self, buf: bytes) -> bool:
        return buf[:10] == bytearray(
            [0x67, 0x69, 0x6D, 0x70, 0x20, 0x78, 0x63, 0x66, 0x20, 0x76]
        )


class Avif(IsoBmff):
    """
    Implements the AVIF image type matcher.
    """

    MIME: str = "image/avif"
    EXTENSION: str = "avif"

    def match(self, buf: bytes) -> bool:
        if not self._is_isobmff(buf):
            return False

        major_brand, minor_version, compatible_brands = self._get_ftyp(buf)
        if major_brand in ["avif", "avis"]:
            return True
        if major_brand in ["mif1", "msf1"] and "avif" in compatible_brands:
            return True
        return False


@dataclass
class Qoi(MagicType):
    """
    Implements the QOI image type matcher.
    """

    MIME: str = "image/qoi"
    EXTENSION: str = "qoi"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 3
            and buf[0] == 0x71
            and buf[1] == 0x6F
            and buf[2] == 0x69
            and buf[3] == 0x66
        )
