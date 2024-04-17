from __future__ import annotations

from typing import Any, Callable, TypeVar


_BaseDecoratedFunc = Callable[..., Any]
DecoratedFunc = TypeVar("DecoratedFunc", bound=_BaseDecoratedFunc)
