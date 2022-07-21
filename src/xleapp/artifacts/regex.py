import typing as t

from dataclasses import dataclass, field


@dataclass
class SearchRegex:
    regex: str = field(init=True)
    processed: bool = field(init=False, compare=False, default=False)

    def __str__(self) -> str:
        return self.regex

    def __hash__(self) -> int:
        return hash(self.regex)
