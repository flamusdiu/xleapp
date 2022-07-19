import functools
import logging
import sqlite3
import typing as t

from ..helpers.types import DecoratedFunc
from ..helpers.search import SearchRegex
from .abstract import Artifact


logger_log = logging.getLogger("xleapp.logfile")


def core_artifact(cls: DecoratedFunc) -> DecoratedFunc:
    """Decorator to mark an artifact as 'core'

    Args:
        cls: The artifact object


    Returns:
        DecoratedFunc: The decorated object
    """

    @functools.wraps(cls)
    def core_wrapper(cls):
        if issubclass(cls, Artifact):
            cls.core = True
            cls.select = True
            return cls
        else:
            raise AttributeError(
                f"Class object {str(cls)} is not an Artifact! "
                f'Error setting property "core_artifact" on class!',
            )

    return t.cast(DecoratedFunc, core_wrapper(cls))


def long_running_process(cls: DecoratedFunc) -> DecoratedFunc:
    """Marks an artifact as a 'long running process'.

    Artifacts marked with this decorator must be manually selected either through
    `--artifact` option in the CLI or in the GUI list. They are never selected manually.

    Args:
        cls: The artifact object

    Returns:
        DecoratedFunc: The decorated object
    """

    @functools.wraps(cls)
    def lrp_wrapper(cls):
        if issubclass(cls, Artifact):
            cls.long_running_process = True
            return cls
        else:
            raise AttributeError(
                f"Class object {str(cls)} is not an Artifact! "
                f'Error setting property "long_running_process" on class!',
            )

    return t.cast(DecoratedFunc, lrp_wrapper(cls))


class Search:
    """Decorator for searching files for an artifact.

    Args:
       file_names_only: Returns only file names (:obj:`Path` objects).
           Defaults to False.
       return_on_first_hit: Returns only the first found file. Defaults to True.
    """

    
    def __init__(
        self,
        func
    ):
        print(f"__init__: {func}")
    
    def __call__(self, func):
        print(f"__call__: {func}")


    def __get__(self, obj, objtype):
        """Support instance methods."""
        return functools.partial(self.__call__, obj)