import struct
from dataclasses import dataclass

from .base import MagicType


@dataclass
class Epub(MagicType):
    """
    Implements the EPUB archive type matcher.
    """

    MIME: str = "application/epub+zip"
    EXTENSION: str = "epub"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 57
            and buf[0] == 0x50
            and buf[1] == 0x4B
            and buf[2] == 0x3
            and buf[3] == 0x4
            and buf[30] == 0x6D
            and buf[31] == 0x69
            and buf[32] == 0x6D
            and buf[33] == 0x65
            and buf[34] == 0x74
            and buf[35] == 0x79
            and buf[36] == 0x70
            and buf[37] == 0x65
            and buf[38] == 0x61
            and buf[39] == 0x70
            and buf[40] == 0x70
            and buf[41] == 0x6C
            and buf[42] == 0x69
            and buf[43] == 0x63
            and buf[44] == 0x61
            and buf[45] == 0x74
            and buf[46] == 0x69
            and buf[47] == 0x6F
            and buf[48] == 0x6E
            and buf[49] == 0x2F
            and buf[50] == 0x65
            and buf[51] == 0x70
            and buf[52] == 0x75
            and buf[53] == 0x62
            and buf[54] == 0x2B
            and buf[55] == 0x7A
            and buf[56] == 0x69
            and buf[57] == 0x70
        )


@dataclass
class Zip(MagicType):
    """
    Implements the Zip archive type matcher.
    """

    MIME: str = "application/zip"
    EXTENSION: str = "zip"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 3
            and buf[0] == 0x50
            and buf[1] == 0x4B
            and (buf[2] == 0x3 or buf[2] == 0x5 or buf[2] == 0x7)
            and (buf[3] == 0x4 or buf[3] == 0x6 or buf[3] == 0x8)
        )


@dataclass
class Tar(MagicType):
    """
    Implements the Tar archive type matcher.
    """

    MIME: str = "application/x-tar"
    EXTENSION: str = "tar"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 261
            and buf[257] == 0x75
            and buf[258] == 0x73
            and buf[259] == 0x74
            and buf[260] == 0x61
            and buf[261] == 0x72
        )


@dataclass
class Rar(MagicType):
    """
    Implements the RAR archive type matcher.
    """

    MIME: str = "application/x-rar-compressed"
    EXTENSION: str = "rar"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 6
            and buf[0] == 0x52
            and buf[1] == 0x61
            and buf[2] == 0x72
            and buf[3] == 0x21
            and buf[4] == 0x1A
            and buf[5] == 0x7
            and (buf[6] == 0x0 or buf[6] == 0x1)
        )


@dataclass
class Gz(MagicType):
    """
    Implements the GZ archive type matcher.
    """

    MIME: str = "application/gzip"
    EXTENSION: str = "gz"

    def match(self, buf: bytes) -> bool:
        return len(buf) > 2 and buf[0] == 0x1F and buf[1] == 0x8B and buf[2] == 0x8


@dataclass
class Bz2(MagicType):
    """
    Implements the BZ2 archive type matcher.
    """

    MIME: str = "application/x-bzip2"
    EXTENSION: str = "bz2"

    def match(self, buf: bytes) -> bool:
        return len(buf) > 2 and buf[0] == 0x42 and buf[1] == 0x5A and buf[2] == 0x68


@dataclass
class SevenZ(MagicType):
    """
    Implements the SevenZ (7z) archive type matcher.
    """

    MIME: str = "application/x-7z-compressed"
    EXTENSION: str = "7z"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 5
            and buf[0] == 0x37
            and buf[1] == 0x7A
            and buf[2] == 0xBC
            and buf[3] == 0xAF
            and buf[4] == 0x27
            and buf[5] == 0x1C
        )


@dataclass
class Pdf(MagicType):
    """
    Implements the PDF archive type matcher.
    """

    MIME: str = "application/pdf"
    EXTENSION: str = "pdf"

    def match(self, buf: bytes) -> bool:
        # Detect BOM and skip first 3 bytes
        if (
            len(buf) > 3 and buf[0] == 0xEF and buf[1] == 0xBB and buf[2] == 0xBF
        ):  # noqa E129
            buf = buf[3:]

        return (
            len(buf) > 3
            and buf[0] == 0x25
            and buf[1] == 0x50
            and buf[2] == 0x44
            and buf[3] == 0x46
        )


@dataclass
class Exe(MagicType):
    """
    Implements the EXE archive type matcher.
    """

    MIME: str = "application/x-msdownload"
    EXTENSION: str = "exe"

    def match(self, buf: bytes) -> bool:
        return len(buf) > 1 and buf[0] == 0x4D and buf[1] == 0x5A


@dataclass
class Swf(MagicType):
    """
    Implements the SWF archive type matcher.
    """

    MIME: str = "application/x-shockwave-flash"
    EXTENSION: str = "swf"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 2
            and (buf[0] == 0x46 or buf[0] == 0x43 or buf[0] == 0x5A)
            and buf[1] == 0x57
            and buf[2] == 0x53
        )


@dataclass
class Rtf(MagicType):
    """
    Implements the RTF archive type matcher.
    """

    MIME: str = "application/rtf"
    EXTENSION: str = "rtf"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 4
            and buf[0] == 0x7B
            and buf[1] == 0x5C
            and buf[2] == 0x72
            and buf[3] == 0x74
            and buf[4] == 0x66
        )


@dataclass
class Nes(MagicType):
    """
    Implements the NES archive type matcher.
    """

    MIME: str = "application/x-nintendo-nes-rom"
    EXTENSION: str = "nes"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 3
            and buf[0] == 0x4E
            and buf[1] == 0x45
            and buf[2] == 0x53
            and buf[3] == 0x1A
        )


@dataclass
class Crx(MagicType):
    """
    Implements the CRX archive type matcher.
    """

    MIME: str = "application/x-google-chrome-extension"
    EXTENSION: str = "crx"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 3
            and buf[0] == 0x43
            and buf[1] == 0x72
            and buf[2] == 0x32
            and buf[3] == 0x34
        )


@dataclass
class Cab(MagicType):
    """
    Implements the CAB archive type matcher.
    """

    MIME: str = "application/vnd.ms-cab-compressed"
    EXTENSION: str = "cab"

    def match(self, buf: bytes) -> bool:
        return len(buf) > 3 and (
            (buf[0] == 0x4D and buf[1] == 0x53 and buf[2] == 0x43 and buf[3] == 0x46)
            or (buf[0] == 0x49 and buf[1] == 0x53 and buf[2] == 0x63 and buf[3] == 0x28)
        )


@dataclass
class Eot(MagicType):
    """
    Implements the EOT archive type matcher.
    """

    MIME: str = "application/octet-stream"
    EXTENSION: str = "eot"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 35
            and buf[34] == 0x4C
            and buf[35] == 0x50
            and (
                (buf[8] == 0x02 and buf[9] == 0x00 and buf[10] == 0x01)
                or (buf[8] == 0x01 and buf[9] == 0x00 and buf[10] == 0x00)
                or (buf[8] == 0x02 and buf[9] == 0x00 and buf[10] == 0x02)
            )
        )


@dataclass
class Ps(MagicType):
    """
    Implements the PS archive type matcher.
    """

    MIME: str = "application/postscript"
    EXTENSION: str = "ps"

    def match(self, buf: bytes) -> bool:
        return len(buf) > 1 and buf[0] == 0x25 and buf[1] == 0x21


@dataclass
class Xz(MagicType):
    """
    Implements the XS archive type matcher.
    """

    MIME: str = "application/x-xz"
    EXTENSION: str = "xz"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 5
            and buf[0] == 0xFD
            and buf[1] == 0x37
            and buf[2] == 0x7A
            and buf[3] == 0x58
            and buf[4] == 0x5A
            and buf[5] == 0x00
        )


@dataclass
class Sqlite(MagicType):
    """
    Implements the Sqlite DB archive type matcher.
    """

    MIME: str = "application/x-sqlite3"
    EXTENSION: str = "sqlite"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 3
            and buf[0] == 0x53
            and buf[1] == 0x51
            and buf[2] == 0x4C
            and buf[3] == 0x69
        )


@dataclass
class Deb(MagicType):
    """
    Implements the DEB archive type matcher.
    """

    MIME: str = "application/x-deb"
    EXTENSION: str = "deb"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 20
            and buf[0] == 0x21
            and buf[1] == 0x3C
            and buf[2] == 0x61
            and buf[3] == 0x72
            and buf[4] == 0x63
            and buf[5] == 0x68
            and buf[6] == 0x3E
            and buf[7] == 0x0A
            and buf[8] == 0x64
            and buf[9] == 0x65
            and buf[10] == 0x62
            and buf[11] == 0x69
            and buf[12] == 0x61
            and buf[13] == 0x6E
            and buf[14] == 0x2D
            and buf[15] == 0x62
            and buf[16] == 0x69
            and buf[17] == 0x6E
            and buf[18] == 0x61
            and buf[19] == 0x72
            and buf[20] == 0x79
        )


@dataclass
class Ar(MagicType):
    """
    Implements the AR archive type matcher.
    """

    MIME: str = "application/x-unix-archive"
    EXTENSION: str = "ar"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 6
            and buf[0] == 0x21
            and buf[1] == 0x3C
            and buf[2] == 0x61
            and buf[3] == 0x72
            and buf[4] == 0x63
            and buf[5] == 0x68
            and buf[6] == 0x3E
        )


@dataclass
class Z(MagicType):
    """
    Implements the Z archive type matcher.
    """

    MIME: str = "application/x-compress"
    EXTENSION: str = "Z"

    def match(self, buf: bytes) -> bool:
        return len(buf) > 1 and (
            (buf[0] == 0x1F and buf[1] == 0xA0) or (buf[0] == 0x1F and buf[1] == 0x9D)
        )


@dataclass
class Lzop(MagicType):
    """
    Implements the Lzop archive type matcher.
    """

    MIME: str = "application/x-lzop"
    EXTENSION: str = "lzo"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 7
            and buf[0] == 0x89
            and buf[1] == 0x4C
            and buf[2] == 0x5A
            and buf[3] == 0x4F
            and buf[4] == 0x00
            and buf[5] == 0x0D
            and buf[6] == 0x0A
            and buf[7] == 0x1A
        )


@dataclass
class Lz(MagicType):
    """
    Implements the Lz archive type matcher.
    """

    MIME: str = "application/x-lzip"
    EXTENSION: str = "lz"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 3
            and buf[0] == 0x4C
            and buf[1] == 0x5A
            and buf[2] == 0x49
            and buf[3] == 0x50
        )


@dataclass
class Elf(MagicType):
    """
    Implements the Elf archive type matcher
    """

    MIME: str = "application/x-executable"
    EXTENSION: str = "elf"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 52
            and buf[0] == 0x7F
            and buf[1] == 0x45
            and buf[2] == 0x4C
            and buf[3] == 0x46
        )


@dataclass
class Lz4(MagicType):
    """
    Implements the Lz4 archive type matcher.
    """

    MIME: str = "application/x-lz4"
    EXTENSION: str = "lz4"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 3
            and buf[0] == 0x04
            and buf[1] == 0x22
            and buf[2] == 0x4D
            and buf[3] == 0x18
        )


@dataclass
class Br(MagicType):
    """Implements the Br image type matcher."""

    MIME: str = "application/x-brotli"
    EXTENSION: str = "br"

    def match(self, buf: bytes) -> bool:
        return buf[:4] == bytearray([0xCE, 0xB2, 0xCF, 0x81])


@dataclass
class Dcm(MagicType):
    """Implements the Dcm image type matcher."""

    MIME: str = "application/dicom"
    EXTENSION: str = "dcm"

    def match(self, buf: bytes) -> bool:
        return buf[128:131] == bytearray([0x44, 0x49, 0x43, 0x4D])


@dataclass
class Rpm(MagicType):
    """Implements the Rpm image type matcher."""

    MIME: str = "application/x-rpm"
    EXTENSION: str = "rpm"

    def match(self, buf: bytes) -> bool:
        return buf[:4] == bytearray([0xED, 0xAB, 0xEE, 0xDB])


@dataclass
class Zstd(MagicType):
    """
    Implements the Zstd archive type matcher.
    https://github.com/facebook/zstd/blob/dev/doc/zstd_compression_format.md
    """

    MIME: str = "application/zstd"
    EXTENSION: str = "zst"
    MAGIC_SKIPPABLE_START = 0x184D2A50
    MAGIC_SKIPPABLE_MASK = 0xFFFFFFF0

    @staticmethod
    def _to_little_endian_int(buf):
        # return int.from_bytes(buf, byteorder='little')
        return struct.unpack("<L", buf)[0]

    def match(self, buf: bytes) -> bool:
        # Zstandard compressed data is made of one or more frames.
        # There are two frame formats defined by Zstandard:
        # Zstandard frames and Skippable frames.
        # See more details from
        # https://tools.ietf.org/id/draft-kucherawy-dispatch-zstd-00.html#rfc.section.2
        is_zstd = (
            len(buf) > 3
            and buf[0] in (0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28)
            and buf[1] == 0xB5
            and buf[2] == 0x2F
            and buf[3] == 0xFD
        )
        if is_zstd:
            return True
        # skippable frames
        if len(buf) < 8:
            return False
        magic = self._to_little_endian_int(buf[:4]) & Zstd.MAGIC_SKIPPABLE_MASK
        if magic == Zstd.MAGIC_SKIPPABLE_START:
            user_data_len = self._to_little_endian_int(buf[4:8])
            if len(buf) < 8 + user_data_len:
                return False
            next_frame = buf[8 + user_data_len :]
            return self.match(next_frame)
        return False
