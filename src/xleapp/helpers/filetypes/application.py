from dataclasses import dataclass

from .base import MagicType


@dataclass
class Wasm(MagicType):
    """Implements the Wasm image type matcher."""

    MIME: str = "application/wasm"
    EXTENSION: str = "wasm"

    def match(self, buf: bytes) -> bool:
        return buf[:8] == bytearray([0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00])
