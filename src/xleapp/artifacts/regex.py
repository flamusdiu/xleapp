import typing as t

from dataclasses import dataclass, field


@dataclass
class SearchRegex:
    regex: str = field(init=True, hash=True)
    processed: bool = field(init=False, hash=False, compare=False, default=False)
