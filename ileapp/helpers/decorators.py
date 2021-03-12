import functools
import logging
import time

import ileapp.globals as g
from ileapp.helpers.utils import get_abstract_artifact

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
    """

    AbstractArtifact = get_abstract_artifact()

    @functools.wraps(cls)
    def core_wrapper(cls):
        if issubclass(cls, AbstractArtifact):
            setattr(cls, 'core', True)
            setattr(cls, 'selected', True)
            return cls
        else:
            raise AttributeError(
                f'Class object {str(cls)} is not an Artifact! '
                f'Error setting property \'core_artifact\' on class!'
            )
    return core_wrapper(cls)


def long_running_process(cls):
    """Decorator to mark an artifact as long running
    """

    AbstractArtifact = get_abstract_artifact()

    @functools.wraps(cls)
    def lrp_wrapper(cls):
        if issubclass(cls, AbstractArtifact):
            setattr(cls, '_long_running_process', True)
            return cls
        else:
            raise AttributeError(
                f'Class object {str(cls)} is not an Artifact! '
                f'Error setting property \'long_running_process\' on class!'
            )
    return lrp_wrapper(cls)


class Search:

    def __init__(self, *args):
        self._search = [*args]

    def __call__(self, func):
        def search_wrapper(cls) -> bool:
            self.files = g.files
            self.regex = g.regex
            self.seeker = g.seeker

            files_found = []
            for r in self._search:
                self.regex[r] += 1
                found = self.seeker.search(r)

                for f in found:
                    self.files[r] = f

                files_found.append((r, self.files.get(r)))
                cls.regex.append([r, [f for f in found]])

            cls.found = files_found
            if cls.processed is True:
                return func(cls)
            return (0, False)

        functools.update_wrapper(search_wrapper, func)
        return search_wrapper
