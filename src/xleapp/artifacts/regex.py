import typing as t

from dataclasses import dataclass, field


@dataclass(unsafe_hash=True)
class SearchRegex:
    regex: str = field(init=True, hash=True)
    processed: bool = field(init=False, hash=False, compare=False, default=False)

    def __str__(self) -> str:
        return self.regex