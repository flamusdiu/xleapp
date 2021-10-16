import functools
import logging
import sqlite3

from ._abstract import Artifact

logger_log = logging.getLogger("xleapp.logfile")


def core_artifact(cls: Artifact):
    """Decorator to mark a core artifact

    Args:
        cls: Artifact class object

    Raises:
        AttributeError

    """

    @functools.wraps(cls)
    def core_wrapper(cls):
        if issubclass(cls, Artifact):
            cls.core = True
            cls.selected = True
            cls.report = False
            return cls
        else:
            raise AttributeError(
                f"Class object {str(cls)} is not an Artifact! "
                f'Error setting property "core_artifact" on class!',
            )

    return core_wrapper(cls)


def long_running_process(cls: Artifact):
    """Decorator to mark an artifact as long running

    Args:
        cls: Artifact class object

    Raises:
        AttributeError

    Returns:
        Artifact: Artifact is marked as long running process
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

    return lrp_wrapper(cls)


class Search:
    def __init__(
        self,
        *args,
        file_names_only: bool = False,
        return_on_first_hit: bool = True,
    ):
        self.return_on_first_hit = return_on_first_hit
        self.file_names_only = file_names_only
        self.search = [*args]

    def __call__(self, func):
        def search_wrapper(cls) -> bool:
            try:
                with cls.context(
                    regex=self.search,
                    file_names_only=self.file_names_only,
                    return_on_first_hit=self.return_on_first_hit,
                ) as artifact:
                    func(artifact)
                    cls.processed = True
            except sqlite3.OperationalError as ex:
                logger_log.error(f"-> Error {ex}")
            return cls.processed

        functools.update_wrapper(search_wrapper, func)
        return search_wrapper
