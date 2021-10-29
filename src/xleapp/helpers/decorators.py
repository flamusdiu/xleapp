import functools
import time
import typing as t


F = t.TypeVar("F", bound=t.Callable[..., t.Any])  # noqa: VNE001


# timer function
def timed(func: F) -> F:
    """Print the runtime of the decorated function"""

    @functools.wraps(func)
    def timed_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        value = func(*args, **kwargs)
        end_time = time.perf_counter()
        run_time = end_time - start_time
        return run_time, value

    return timed_wrapper
