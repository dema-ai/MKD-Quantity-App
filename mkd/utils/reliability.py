import time, functools, random

def retry(max_attempts=3, base=0.5, jitter=0.2, exceptions=(Exception,)):
    def deco(fn):
        @functools.wraps(fn)
        def wrap(*a, **k):
            for attempt in range(max_attempts):
                try:
                    return fn(*a, **k)
                except exceptions:
                    if attempt == max_attempts - 1:
                        raise
                    time.sleep(base * (2 ** attempt) + random.uniform(0, jitter))
        return wrap
    return deco
