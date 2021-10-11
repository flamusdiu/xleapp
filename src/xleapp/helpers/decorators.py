import functools
import logging
import time


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
