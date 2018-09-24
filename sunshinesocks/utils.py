import os
import re
import platform


def port(raw):
    var = int(raw)
    if float(raw) != var or var not in range(65536):
        raise ValueError('Invalid port number')
    return var


LINUX_VERSION_PATTERN = re.compile(r'^((\d+\.)+\d+).*')


def linux_version(release):
    match = LINUX_VERSION_PATTERN.match(release)
    if match:
        return tuple(map(int, match.group(1).split('.')))
    return ()


ENABLE_CLIENT_TFO = platform.system() == 'Linux' and\
                    linux_version(platform.release()) > (3, 6)

ENABLE_SERVER_TFO = platform.system() == 'Linux' and\
                    linux_version(platform.release()) > (3, 7)

ENABLE_WORKER = ENABLE_DAEMON = os.name == 'posix'
