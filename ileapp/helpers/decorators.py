import functools
import time
import ileapp.globals


# timer function
def timer(func):
    """Print the runtime of the decorated function"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        value = func(*args, **kwargs)
        end_time = time.perf_counter()
        run_time = end_time - start_time
        return value, run_time
    return wrapper


def template(func):
    """[summary]

    Args:
        func ([type]): [description]
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        jinja = ileapp.globals.jinja
        kwargs['jinja'] = jinja
        value = func(*args, **kwargs)
        return value
    return wrapper
