import abc
import codecs
from dataclasses import dataclass

from .base import MagicType


@dataclass
class IsoBmff(abc.ABC, MagicType):
    """
    Implements the ISO-BMFF base type.
    """

    def _is_isobmff(self, buf: bytes) -> bool:
        if len(buf) < 16 or buf[4:8] != b"ftyp":
            return False
        if len(buf) < int(codecs.encode(buf[0:4], "hex"), 16):
            return False
        return True

    def _get_ftyp(self, buf: bytes) -> tuple[str, int, list[str]]:
        ftyp_len: int = int(codecs.encode(buf[0:4], "hex"), 16)
        major_brand: str = buf[8:12].decode(errors="ignore")
        minor_version: int = int(codecs.encode(buf[12:16], "hex"), 16)
        compatible_brands: list = []
        for i in range(16, ftyp_len, 4):
            compatible_brands.append(buf[i : i + 4].decode(errors="ignore"))

        return major_brand, minor_version, compatible_brands
