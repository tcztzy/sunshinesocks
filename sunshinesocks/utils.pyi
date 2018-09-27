import functools
from typing import Optional, Any


def lru_cache(maxsize: Optional[int] = 128, typed: bool = False,
              days: float = 0, seconds: float = 0, microseconds: float = 0,
              milliseconds: float = 0, minutes: float = 0, hours: float = 0,
              weeks: float = 0) -> functools.lru_cache: ...


def port(raw: Any) -> int: ...

ENABLE_DAEMON: bool
ENABLE_WORKER: bool
