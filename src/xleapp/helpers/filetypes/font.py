from .base import MagicType


class Woff(MagicType):
    """
    Implements the WOFF font type matcher.
    """

    MIME: str = "application/font-woff"
    EXTENSION: str = "woff"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 7
            and buf[0] == 0x77
            and buf[1] == 0x4F
            and buf[2] == 0x46
            and buf[3] == 0x46
            and (
                (buf[4] == 0x00 and buf[5] == 0x01 and buf[6] == 0x00 and buf[7] == 0x00)
                or (
                    buf[4] == 0x4F
                    and buf[5] == 0x54
                    and buf[6] == 0x54
                    and buf[7] == 0x4F
                )
                or (
                    buf[4] == 0x74
                    and buf[5] == 0x72
                    and buf[6] == 0x75
                    and buf[7] == 0x65
                )
            )
        )


class Woff2(MagicType):
    """
    Implements the WOFF2 font type matcher.
    """

    MIME: str = "application/font-woff"
    EXTENSION: str = "woff2"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 7
            and buf[0] == 0x77
            and buf[1] == 0x4F
            and buf[2] == 0x46
            and buf[3] == 0x32
            and (
                (buf[4] == 0x00 and buf[5] == 0x01 and buf[6] == 0x00 and buf[7] == 0x00)
                or (
                    buf[4] == 0x4F
                    and buf[5] == 0x54
                    and buf[6] == 0x54
                    and buf[7] == 0x4F
                )
                or (
                    buf[4] == 0x74
                    and buf[5] == 0x72
                    and buf[6] == 0x75
                    and buf[7] == 0x65
                )
            )
        )


class Ttf(MagicType):
    """
    Implements the TTF font type matcher.
    """

    MIME: str = "application/font-sfnt"
    EXTENSION: str = "ttf"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 4
            and buf[0] == 0x00
            and buf[1] == 0x01
            and buf[2] == 0x00
            and buf[3] == 0x00
            and buf[4] == 0x00
        )


class Otf(MagicType):
    """
    Implements the OTF font type matcher.
    """

    MIME: str = "application/font-sfnt"
    EXTENSION: str = "otf"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 4
            and buf[0] == 0x4F
            and buf[1] == 0x54
            and buf[2] == 0x54
            and buf[3] == 0x4F
            and buf[4] == 0x00
        )
