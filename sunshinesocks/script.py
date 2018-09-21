import argparse
from argparse import FileType, SUPPRESS
from ipaddress import ip_address

import sunshinesocks

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


class SunshineSocksHelpFormatter(argparse.RawTextHelpFormatter,
                                 argparse.ArgumentDefaultsHelpFormatter):
    pass


class SunshineSocksArgumentParser(argparse.ArgumentParser):
    def __init__(self):
        super().__init__(
            prog='sunshinesocks',
            description=SUNSHINESOCKS_DESCRIPTION,
            formatter_class=SunshineSocksHelpFormatter,
            add_help=False
        )
        self.add_arguments()

    def add_arguments(self):
        self.add_proxy_option_argument_group()
        self.add_general_option_argument_group()

    def add_proxy_option_argument_group(self):
        group = self.add_argument_group('Proxy Option')
        group.add_argument('-c', type=FileType('r', encoding='UTF-8'),
                           metavar='CONFIG', help='path to config file'),
        group.add_argument('-s', dest='server', type=ip_address,
                           metavar='SERVER_ADDR',
                           default=ip_address('0.0.0.0'),
                           help='server address')
        group.add_argument('-p', dest='server_port', type=int, default=1984,
                           metavar='SERVER_PORT', help='server port')
        group.add_argument('-k', dest='password', metavar='PASSWORD',
                           required=True, help='password', default=SUPPRESS)
        group.add_argument('-m', dest='method', choices=METHOD_CHOICES,
                           required=True, metavar='METHOD', help=METHOD_HELP,
                           default=SUPPRESS)
        group.add_argument('-t', dest='timeout', type=int, default=300,
                           metavar='TIMEOUT', help='timeout in second')
        group.add_argument('-a', dest='one-time-auth', action='store_true',
                           help='one time auth', default=SUPPRESS)
        group.add_argument('--fast-open', action='store_true',
                           default=SUPPRESS,
                           help='use TCP_FASTOPEN, requires Linux 3.7+')
        group.add_argument('--worker', type=int, default=SUPPRESS,
                           help='number of workers, available on Unix/Linux')
        group.add_argument('--prefer-ipv6', help='resolve ipv6 address first',
                           default=SUPPRESS)

    def add_general_option_argument_group(self):
        group = self.add_argument_group('General Option')
        group.add_argument('-h', '--help', action='help',
                           help='show this help message and exit')
        group.add_argument('-v', '--verbose', action='count', default=SUPPRESS,
                           help='verbose mode, -vv for higher level')
        group.add_argument('-q', '--quiet', action='count', default=SUPPRESS,
                           help='quiet mode, -qq for higher level')
        group.add_argument('--version', action='version',
                           version=f'%(prog)s {sunshinesocks.__version__}')
