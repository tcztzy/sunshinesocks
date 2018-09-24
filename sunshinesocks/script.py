from argparse import (ArgumentParser,
                      RawTextHelpFormatter,
                      ArgumentDefaultsHelpFormatter,
                      FileType,
                      SUPPRESS)
from enum import Enum

import sunshinesocks
from sunshinesocks.utils import (port,
                                 ENABLE_CLIENT_TFO,
                                 ENABLE_SERVER_TFO,
                                 ENABLE_DAEMON,
                                 ENABLE_WORKER)

SUNSHINESOCKS_DESCRIPTION = f'''\
{sunshinesocks.__doc__}

You can supply configurations via either config file or command line arguments.
'''

METHOD_HELP = '''\
encryption method, default: aes-256-cfb
Sodium:
    chacha20-poly1305, chacha20-ietf-poly1305,
    xchacha20-ietf-poly1305,
    sodium:aes-256-gcm,
    salsa20, chacha20, chacha20-ietf.
Sodium 1.0.12:
    xchacha20
OpenSSL:
    aes-{128|192|256}-gcm, aes-{128|192|256}-cfb,
    aes-{128|192|256}-ofb, aes-{128|192|256}-ctr,
    camellia-{128|192|256}-cfb,
    bf-cfb, cast5-cfb, des-cfb, idea-cfb,
    rc2-cfb, seed-cfb,
    rc4, rc4-md5, table.
OpenSSL 1.1:
    aes-{128|192|256}-ocb
mbedTLS:
    mbedtls:aes-{128|192|256}-cfb128,
    mbedtls:aes-{128|192|256}-ctr,
    mbedtls:camellia-{128|192|256}-cfb128,
    mbedtls:aes-{128|192|256}-gcm
'''

lengths = (128, 192, 256)

AES_MODES = ('gcm', 'cfb', 'ofb', 'ctr', 'ocb')

METHOD_CHOICES = (
    'chacha20-poly1305', 'chacha20-ietf-poly1305', 'xchacha20-ietf-poly1305',
    'sodium:aes-256-gcm', 'salsa20', 'chacha20', 'chacha20-ietf', 'xchacha20',
    *('aes-{}-{}'.format(l, m) for l in lengths for m in AES_MODES),
    *('camellia-{}-cfb'.format(l) for l in lengths),  'bf-cfb', 'cast5-cfb',
    'des-cfb', 'idea-cfb', 'rc2-cfb', 'seed-cfb', 'rc4', 'rc4-md5', 'table',
    *('mbedtls:aes-{}-{}'.format(l, m)
      for l in lengths for m in ('ctr', 'gcm', 'cfb128')),
    *('mbedtls:camellia-{}-cfb128'.format(l) for l in lengths),
)


class SunshineSocksHelpFormatter(RawTextHelpFormatter,
                                 ArgumentDefaultsHelpFormatter):
    pass


class Role(Enum):
    SERVER = 'server'
    CLIENT = 'client'


def _init_parser(_parser, role: Role):
    group = _parser.add_argument_group('Proxy Option')
    group.add_argument('-c', type=FileType('r', encoding='UTF-8'),
                       metavar='CONFIG', help='path to config file',
                       default=SUPPRESS)
    group.add_argument('-s', dest='server', metavar='SERVER_ADDR',
                       help='server address',
                       default='0.0.0.0' if role == Role.SERVER else SUPPRESS)
    group.add_argument('-p', dest='server_port', type=port, default=1984,
                       metavar='SERVER_PORT', help='server port')
    if role == Role.CLIENT:
        group.add_argument('-b', dest='local_address', default='127.0.0.1',
                           help='local binding address', metavar='LOCAL_ADDR')
        group.add_argument('-l', type=port, default=1080, dest='local_port',
                           help='local port')
    group.add_argument('-k', dest='password', metavar='PASSWORD',
                       help='password', default=SUPPRESS)
    group.add_argument('-m', dest='method', choices=METHOD_CHOICES,
                       metavar='METHOD', help=METHOD_HELP, default=SUPPRESS)
    group.add_argument('-t', dest='timeout', type=int, default=300,
                       metavar='TIMEOUT', help='timeout in second')
    group.add_argument('-a', dest='one-time-auth', action='store_true',
                       help='one time auth', default=SUPPRESS)
    if (role == Role.SERVER and ENABLE_SERVER_TFO) or\
            (role == Role.CLIENT and ENABLE_CLIENT_TFO):
        group.add_argument('--fast-open', action='store_true',
                           default=SUPPRESS, help='use TCP_FASTOPEN')
    if role == Role.SERVER:
        if ENABLE_WORKER:
            group.add_argument('--worker', type=int, default=SUPPRESS,
                               help='number of workers')
        group.add_argument('--forbidden-ip', metavar='IPLIST',
                           help='comma seperated IP list forbidden to connect')
    group.add_argument('--prefer-ipv6', action='store_true', default=SUPPRESS,
                       help='resolve ipv6 address first')

    group = _parser.add_argument_group('General Option')
    group.add_argument('-h', '--help', action='help',
                       help='show this help message and exit')
    if ENABLE_DAEMON:
        group.add_argument('-d', choices=('start', 'stop', 'restart'),
                           default=SUPPRESS, help='daemon mode', dest='daemon')
        group.add_argument('--pid-file', help='pid file for daemon mode',
                           default=SUPPRESS)
        group.add_argument('--log-file', help='log file for daemon mode',
                           default=SUPPRESS)
        group.add_argument('--user', help='username to run as',
                           default=SUPPRESS)
    group.add_argument('-v', '--verbose', action='count', default=SUPPRESS,
                       help='verbose mode, -vv for higher level')
    group.add_argument('-q', '--quiet', action='count', default=SUPPRESS,
                       help='quiet mode, -qq for higher level')
    group.add_argument('--version', action='version',
                       version=f'%(prog)s {sunshinesocks.__version__}')


parser = ArgumentParser(description=SUNSHINESOCKS_DESCRIPTION,
                        formatter_class=SunshineSocksHelpFormatter,
                        # add_help=False,
                        epilog='Online help: '
                               '<https://github.com/tcztzy/sunshinesocks>')
subparsers = parser.add_subparsers(dest='subcommand', help='hehe')
server_parser = subparsers.add_parser(
    'server', description=SUNSHINESOCKS_DESCRIPTION,
    formatter_class=SunshineSocksHelpFormatter, add_help=False
)
_init_parser(server_parser, Role.SERVER)
client_parser = subparsers.add_parser(
    'client', description=SUNSHINESOCKS_DESCRIPTION,
    formatter_class=SunshineSocksHelpFormatter, add_help=False
)
_init_parser(client_parser, Role.CLIENT)
help_parser = subparsers.add_parser('help', add_help=False)
help_parser.add_argument('subcommand-help')


def main():
    parser.parse_args()
    args = parser.parse_args()
    print(vars(args))


if __name__ == '__main__':
    main()
