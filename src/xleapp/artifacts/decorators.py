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

    search: dict[str, set[SearchRegex]] = dict()

    def __init__(
        self,
        name,
        regex,
        file_names_only: bool = False,
        return_on_first_hit: bool = True,
    ):
        self.return_on_first_hit = return_on_first_hit
        self.file_names_only = file_names_only
        if not name in self.search.keys():
            self.search[name] = set()
        self.search[name].add(SearchRegex(regex))

    def __call__(self, func):
        def search_wrapper(cls) -> bool:
            try:
                cls.regex = self.search[f"{cls.name}__{cls.category}"]
                with cls.context(
                    file_names_only=self.file_names_only,
                    return_on_first_hit=self.return_on_first_hit,
                ) as artifact:
                    if artifact.found:
                        func(artifact)
                    cls.processed = True
            except sqlite3.OperationalError as ex:
                logger_log.error(f"-> Error {ex}")
            return cls.processed
        
        functools.update_wrapper(search_wrapper, func)
        return search_wrapper



    def __get__(self, obj, objtype):
        """Support instance methods."""
        return functools.partial(self.__call__, obj)