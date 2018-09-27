import asyncio
from ipaddress import ip_address
from pathlib import Path

import os
import socket
import struct
import warnings
try:
    import winreg
except ImportError:
    winreg = None
try:
    import uvloop
    asyncio.set_event_loop(uvloop.new_event_loop())
except ImportError:
    pass

from sunshinesocks.utils import lru_cache


GOOGLE_PUBLIC_DNS = ['8.8.8.8', '8.8.4.4',
                     '2001:4860:4860::8888', '2001:4860:4860::8844']

QTYPE_A = 1
QTYPE_NS = 2
QTYPE_CNAME = 3
QTYPE_SOA = 6
QTYPE_WKS = 11
QTYPE_PTR = 12
QTYPE_HINFO = 13
QTYPE_MX = 15
QTYPE_AAAA = 28
QTYPE_AXFR = 252
QTYPE_ANY = 255
QCLASS_IN = 1


class DNSProtocol(asyncio.DatagramProtocol):
    """
    Flags
    """
    def __init__(self, hostname, qtype):
        self._hostname = hostname
        self._qtype = qtype
        self._loop = asyncio.get_event_loop()
        self._transport = None

    @property
    def _message(self):
        request_id = os.urandom(2)
        header = struct.pack('!BBHHHH', 1, 0, 1, 0, 0, 0)
        address = self._hostname.strip('.')
        labels = address.split('.')
        results = []
        for label in labels:
            label_length = len(label)
            if label_length > 63:
                raise ValueError('Label length over 63.')
            results.append(chr(label_length))
            results.append(bytes(label, 'UTF-8'))
        results.append(b'\0')
        qtype_qclass = struct.pack('!HH', self._qtype, QCLASS_IN)
        return request_id + header + b''.join(results) + qtype_qclass

    def connection_made(self, transport):
        self._transport = transport
        print('Send:', self._hostname)
        self._transport.sendto(self._message)

    def datagram_received(self, data, addr):
        print("Received:", data.decode())

        print("Close the socket")
        self._transport.close()

    def error_received(self, exc):
        print('Error received:', exc)

    def connection_lost(self, exc):
        print("Socket closed, stop the event loop")
        self._loop.stop()


class DNSResolver:
    def __init__(self):
        self._loop = asyncio.get_event_loop()

    @lru_cache(seconds=300)
    async def resolve(self, hostname):
        transport, protocol = await self._loop.create_datagram_endpoint(
            lambda: DNSProtocol(hostname, QTYPE_A),
            remote_addr=('8.8.8.8', 53)
        )
        self._loop.run_forever()
        transport.close()
        self._loop.close()

    def _parse_nameserver(self):
        self._servers = []
        if os.name == 'posix':
            resolv_conf = Path('/etc/resolv.conf')
            if resolv_conf.exists():
                with resolv_conf.open() as f:
                    for line_no, line in enumerate(f.readlines()):
                        line = line.strip()
                        if line and line.startswith('nameserver'):
                            parts = line.split()
                            if len(parts) < 2:
                                continue

                            server = parts[1]
                            try:
                                self._servers.append(ip_address(server))
                            except ValueError as e:
                                warnings.warn(f'warning: line {line_no} at '
                                              f'{resolv_conf}:\n    {e}')
        elif os.name == 'nt' and winreg is not None:
            subkey = r'SYSTEM\CurrentControlSet\Services\Tcpip\Parameters'
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey) as params:
                nameserver, _ = winreg.QueryValueEx(params, 'NameServer')
                with winreg.OpenKey(params, 'Interfaces') as interfaces:
                    n, _, __ = winreg.QueryInfoKey(interfaces)
                    for i in range(n):
                        with winreg.OpenKey(interfaces,
                                            winreg.EnumKey(interfaces, i))\
                                as interface:
                            try:
                                ns, _ = winreg.QueryValueEx(interface,
                                                            'NameServer')
                                if ns:
                                    nameserver += ',' + ns
                            except FileNotFoundError:
                                pass
                for ns in set(nameserver.split()):
                    self._servers.append(ip_address(ns))

        if not self._servers:
            self._servers = GOOGLE_PUBLIC_DNS

    def _parse_hosts(self):
        self._hosts = {}
        if os.name == 'nt' and winreg is not None:
            subkey = r'SYSTEM\CurrentControlSet\Services\Tcpip\Parameters'
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey) as params:
                data_base_path, _ = winreg.QueryValueEx(params, 'DataBasePath')
                base_path = winreg.ExpandEnvironmentStrings(data_base_path)
                hosts = Path(base_path, 'hosts')
        elif os.name == 'posix':
            hosts = Path('/etc/hosts')
        else:
            hosts = object()
            hosts.exists = lambda: False
        if hosts.exists():
            with hosts.open('rb') as f:
                for line in f.readlines():
                    line = line.strip()
                    parts = line.split()
                    if len(parts) < 2:
                        continue

                    ip = parts[0]
                    try:
                        ip_address(ip)
                    except ValueError:
                        continue

                    for i in range(1, len(parts)):
                        hostname = parts[i]
                        if hostname:
                            self._hosts[hostname] = ip
        else:
            self._hosts['localhost'] = '127.0.0.1'
