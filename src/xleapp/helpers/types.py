from typing import Any, Callable, TypeVar


_BaseDecoratedFunc = Callable[..., Any]
DecoratedFunc = TypeVar('DecoratedFunc', bound=_BaseDecoratedFunc)
