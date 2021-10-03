import functools
import logging
import time

from xleapp.artifacts.abstract import AbstractArtifact

logger = logging.getLogger(__name__)


# timer function
def timed(func):
    """Print the runtime of the decorated function"""

    @functools.wraps(func)
    def timed_wrapper(*args, **kwargs) -> float:
        start_time = time.perf_counter()
        value = func(*args, **kwargs)
        end_time = time.perf_counter()
        run_time = end_time - start_time
        return run_time, value

    return timed_wrapper


def core_artifact(cls):
    """Decorator to mark a core artifact

    Args:
        cls: AbstractArtifact class object

    Raises:
        AttributeError

    Returns:
        AbstractArtifact: Artifact is marked as core and selected
    """

    @functools.wraps(cls)
    def core_wrapper(cls):
        if issubclass(cls, AbstractArtifact):
            cls.core = True
            cls.selected = True
            return cls
        else:
            raise AttributeError(
                f"Class object {str(cls)} is not an Artifact! "
                f'Error setting property "core_artifact" on class!',
            )

    return core_wrapper(cls)


def long_running_process(cls):
    """Decorator to mark an artifact as long running

    Args:
        cls: AbstractArtifact class object

    Raises:
        AttributeError

    Returns:
        AbstractArtifact: Artifact is marked as long running process
    """

    @functools.wraps(cls)
    def lrp_wrapper(cls):
        if issubclass(cls, AbstractArtifact):
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
                return cls.processed
            except Exception as ex:
                logging.error(f"-> Error {ex}", extra={"flow": "no_filter"})

        functools.update_wrapper(search_wrapper, func)
        return search_wrapper
