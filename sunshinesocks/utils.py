import functools
import os
from datetime import datetime, timedelta


def lru_cache(maxsize=None, typed=False, **timedelta_kwargs):
    def _wrapper(f):
        update_delta = timedelta(**timedelta_kwargs)
        next_update = datetime.utcnow() + update_delta
        # Apply @lru_cache to f with no cache size limit
        f = functools.lru_cache(maxsize, typed)(f)

        @functools.wraps(f)
        def _wrapped(*args, **kwargs):
            nonlocal next_update
            now = datetime.utcnow()
            if now >= next_update:
                f.cache_clear()
                next_update = now + update_delta
            return f(*args, **kwargs)

        return _wrapped

    return _wrapper


def port(raw):
    var = int(raw)
    if float(raw) != var or var not in range(65536):
        raise ValueError('Invalid port number')
    return var


ENABLE_WORKER = ENABLE_DAEMON = os.name == 'posix'
