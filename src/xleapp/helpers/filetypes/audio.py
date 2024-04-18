from .base import MagicType


class Midi(MagicType):
    """
    Implements the Midi audio type matcher.
    """

    MIME: str = "audio/midi"
    EXTENSION: str = "midi"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 3
            and buf[0] == 0x4D
            and buf[1] == 0x54
            and buf[2] == 0x68
            and buf[3] == 0x64
        )


class Mp3(MagicType):
    """
    Implements the MP3 audio type matcher.
    """

    MIME: str = "audio/mpeg"
    EXTENSION: str = "mp3"

    def match(self, buf: bytes) -> bool:
        if len(buf) > 2:
            if buf[0] == 0x49 and buf[1] == 0x44 and buf[2] == 0x33:
                return True

            if buf[0] == 0xFF:
                if (
                    buf[1] == 0xE2  # MPEG 2.5 with error protection
                    or buf[1] == 0xE3  # MPEG 2.5 w/o error protection
                    or buf[1] == 0xF2  # MPEG 2 with error protection
                    or buf[1] == 0xF3  # MPEG 2 w/o error protection
                    or buf[1] == 0xFA  # MPEG 1 with error protection
                    or buf[1] == 0xFB  # MPEG 1 w/o error protection
                ):
                    return True
        return False


class M4a(MagicType):
    """
    Implements the M4A audio type matcher.
    """

    MIME: str = "audio/mp4"
    EXTENSION: str = "m4a"

    def match(self, buf: bytes) -> bool:
        return len(buf) > 10 and (
            (
                buf[4] == 0x66
                and buf[5] == 0x74
                and buf[6] == 0x79
                and buf[7] == 0x70
                and buf[8] == 0x4D
                and buf[9] == 0x34
                and buf[10] == 0x41
            )
            or (buf[0] == 0x4D and buf[1] == 0x34 and buf[2] == 0x41 and buf[3] == 0x20)
        )


class Ogg(MagicType):
    """
    Implements the OGG audio type matcher.
    """

    MIME: str = "audio/ogg"
    EXTENSION: str = "ogg"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 3
            and buf[0] == 0x4F
            and buf[1] == 0x67
            and buf[2] == 0x67
            and buf[3] == 0x53
        )


class Flac(MagicType):
    """
    Implements the FLAC audio type matcher.
    """

    MIME: str = "audio/x-flac"
    EXTENSION: str = "flac"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 3
            and buf[0] == 0x66
            and buf[1] == 0x4C
            and buf[2] == 0x61
            and buf[3] == 0x43
        )


class Wav(MagicType):
    """
    Implements the WAV audio type matcher.
    """

    MIME: str = "audio/x-wav"
    EXTENSION: str = "wav"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 11
            and buf[0] == 0x52
            and buf[1] == 0x49
            and buf[2] == 0x46
            and buf[3] == 0x46
            and buf[8] == 0x57
            and buf[9] == 0x41
            and buf[10] == 0x56
            and buf[11] == 0x45
        )


class Amr(MagicType):
    """
    Implements the AMR audio type matcher.
    """

    MIME: str = "audio/amr"
    EXTENSION: str = "amr"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 11
            and buf[0] == 0x23
            and buf[1] == 0x21
            and buf[2] == 0x41
            and buf[3] == 0x4D
            and buf[4] == 0x52
            and buf[5] == 0x0A
        )


class Aac(MagicType):
    """Implements the Aac audio type matcher."""

    MIME: str = "audio/aac"
    EXTENSION: str = "aac"

    def match(self, buf: bytes) -> bool:
        return buf[:2] == bytearray([0xFF, 0xF1]) or buf[:2] == bytearray([0xFF, 0xF9])


class Aiff(MagicType):
    """
    Implements the AIFF audio type matcher.
    """

    MIME: str = "audio/x-aiff"
    EXTENSION: str = "aiff"

    def match(self, buf: bytes) -> bool:
        return (
            len(buf) > 11
            and buf[0] == 0x46
            and buf[1] == 0x4F
            and buf[2] == 0x52
            and buf[3] == 0x4D
            and buf[8] == 0x41
            and buf[9] == 0x49
            and buf[10] == 0x46
            and buf[11] == 0x46
        )
