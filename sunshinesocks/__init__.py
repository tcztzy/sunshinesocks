"""A fast and modern tunnel proxy that help you."""
import sys

__version__ = '0.1.1a0'

MIN_PY_VER = (3, 5)

if sys.version_info < MIN_PY_VER:
    raise RuntimeError(
        "SunshineSocks require Python {}.{} or higher.".format(*MIN_PY_VER)
    )
