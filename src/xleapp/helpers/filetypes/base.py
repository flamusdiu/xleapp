import abc
from dataclasses import dataclass, field


@dataclass
class MagicType(abc.ABC):
    """
    Represents the file type object inherited by
    specific file type matchers.
    Provides convenient accessor and helper methods.
    """

    MIME: str = field(init=False)
    EXTENSION: str = field(init=False)

    def is_extension(self, extension: str) -> bool:
        return self.EXTENSION is extension

    def is_mime(self, mime: str) -> bool:
        return self.EXTENSION is mime

    def match(self, buf: bytes) -> bool | bytes:
        raise NotImplementedError
