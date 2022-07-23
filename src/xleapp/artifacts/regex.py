from dataclasses import dataclass, field


@dataclass
class Regex:
    regex: str = field(init=True)
    processed: bool = field(init=False, compare=False, default=False)
    file_names_only: bool = field(init=True, compare=False, default=False)
    return_on_first_hit: bool = field(init=True, compare=False, default=True)

    def __str__(self) -> str:
        return self.regex

    def __hash__(self) -> int:
        return hash(self.regex)
