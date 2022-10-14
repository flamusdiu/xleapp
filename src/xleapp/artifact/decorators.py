from __future__ import annotations

import functools
import logging
import sqlite3
import typing as t

from xleapp.helpers.types import DecoratedFunc

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


def artifact_process(cls: DecoratedFunc) -> DecoratedFunc:
    @functools.wraps(cls)
    def process_wrapper(cls) -> None:
        msg_artifact = f"{cls.category} [{cls.cls_name}] artifact"
        logger_log.info(f"\n{msg_artifact} processing...")
        cls.process_time, _ = cls.process()
        if not cls.processed:
            logger_log.warn("-> Failed to processed!")
        logger_log.info(f"{msg_artifact} finished in {cls.process_time:.2f}s")

    return t.cast(DecoratedFunc, process_wrapper)


class Search:
    """Decorator for searching files for an artifact.

    Args:
       file_names_only: Returns only file names (:obj:`Path` objects).
           Defaults to False.
       return_on_first_hit: Returns only the first found file. Defaults to True.
    """

    def __init__(
        self,
        search: str,
        *,
        file_names_only: bool = False,
        return_on_first_hit: bool = True,
    ):
        self.search = (search, file_names_only, return_on_first_hit)

    def __call__(self, func):
        def search_wrapper(cls: Artifact) -> bool:
            try:
                cls.regex = self.search
                with cls.context() as artifact:
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

    def __repr__(self) -> str:
        return f"Search(*{self.search!r})"

    def __str__(self) -> str:
        return (
            f"Search {self.search[0]!r}; file_names_only = {self.search[1]!r}; "
            f"return_on_first_hit = {self.search[2]!r}"
        )
