import functools
import logging
import time

import ileapp.artifacts
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

    def __init__(self, *args,
                 file_names_only: bool = False,
                 return_on_first_hit: bool = True):
        self.return_on_first_hit = return_on_first_hit
        self.file_names_only = file_names_only
        self.search = [*args]

    def __call__(self, func):
        def search_wrapper(cls) -> bool:
            self.seeker = g.seeker
            self.files = g.seeker.file_handles
            self.regex = g.seeker.regex
            current_artifact_name = type(cls).__name__.lower()

            for r in self.search:
                results = []
                print(self.regex, len(self.regex[r]) > 0)
                if len(self.regex[r]) > 0:
                    previous_artifact = list(self.regex[r])[0]
                    previous_artifact_cls = ileapp.artifacts.services.get(previous_artifact)
                    print(previous_artifact, previous_artifact_cls)
                    for previous_regex, files in previous_artifact_cls.regex:
                        if previous_regex == r:
                            cls.found.extend([self.files[r]])
                            cls.regex.append([r, files])
                else:
                    try:
                        if self.return_on_first_hit:
                            results = [next(self.seeker.search(r))]
                        else:
                            results = list(self.seeker.search(r))
                    except StopIteration:
                        results = None

                    if results is not None:
                        self.files.add(r, results, self.file_names_only)
                        cls.found.extend([self.files[r]])
                        cls.regex.append([r, results])

                self.regex[r].add(current_artifact_name)

            if cls.processed is True:
                if isinstance(cls.found[0], list) or len(cls.found) == 1:
                    cls.found = cls.found[0]
                return func(cls)
            return (0, False)

        functools.update_wrapper(search_wrapper, func)
        return search_wrapper
