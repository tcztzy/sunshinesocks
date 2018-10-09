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


# rfc1035
# format
# +---------------------+
# |        Header       |
# +---------------------+
# |       Question      | the question for the name server
# +---------------------+
# |        Answer       | RRs answering the question
# +---------------------+
# |      Authority      | RRs pointing toward an authority
# +---------------------+
# |      Additional     | RRs holding additional information
# +---------------------+
#
# header
#
#   0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F
# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
# |                      ID                       |
# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
# |QR|   Opcode  |AA|TC|RD|RA| (zero) |   RCODE   |
# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
# |                    QDCOUNT                    |
# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
# |                    ANCOUNT                    |
# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
# |                    NSCOUNT                    |
# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
# |                    ARCOUNT                    |
# +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+


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
QR_QUERY = 0
QR_RESPONSE = 1


class DNSResponse:
    def __init__(self, data):
        (self.transaction_id,
         self.flags,
         self.questions,
         self.answer_prs,
         self.authority_prs,
         self.additional_prs) = struct.unpack('!HHHHHH', data[:12])
        self._parse_flags()
        q = self.questions
        questions = []
        pointer = 12
        label_length = data[pointer]
        while q > 0:
            question = []
            while label_length > 0:
                pointer += 1
                question.append(data[pointer:pointer+label_length])
                pointer += label_length
                label_length = data[pointer]
            questions.append(b'.'.join(question))
            q -= 1
        print(questions)

    def _parse_flags(self):
        self.qr = (self.flags & 0x8000) >> 15
        self.opcode = (self.flags & 0x7800) >> 11
        self.aa = (self.flags & 0x0400) >> 10
        self.tc = (self.flags & 0x0200) >> 9
        self.rd = (self.flags & 0x0100) >> 8
        self.ra = (self.flags & 0x0080) >> 7
        self.rcode = self.flags & 0x000f

    def __str__(self):
        return '<{} {}>'.format(self.__class__.__name__, self.transaction_id)


class DNSProtocol(asyncio.DatagramProtocol):

    def __init__(self, hostname, qtype):
        self._hostname = hostname
        self._qtype = qtype
        self._loop = asyncio.get_event_loop()
        self._transport = None
        self.result = None
        self._transaction_id = os.urandom(2)

    @property
    def _message(self):
        header = struct.pack('!BBHHHH', 1, 0, 1, 0, 0, 0)
        address = self._hostname.strip('.')
        labels = address.split('.')
        results = []
        for label in labels:
            label_length = len(label)
            if label_length > 63:
                raise ValueError('Label length over 63.')
            results.append(bytes(chr(label_length), 'UTF-8'))
            results.append(bytes(label, 'UTF-8'))
        results.append(b'\0')
        qtype_qclass = struct.pack('!HH', self._qtype, QCLASS_IN)
        return self._transaction_id + header + b''.join(results) + qtype_qclass

    def connection_made(self, transport):
        self._transport = transport
        self._transport.sendto(self._message)

    def datagram_received(self, data, addr):
        self._transport.close()
        response = DNSResponse(data)
        if response.transaction_id != int(self._transaction_id.hex(), 16):
            raise IOError('mismatch transaction id')
        print(response)
        print(data)

    def error_received(self, exc):
        print('Error received:', exc)

    def connection_lost(self, exc):
        print("Socket closed, stop the event loop")
        self._loop.stop()


class DNSResolver:
    def __init__(self):
        self._loop = asyncio.get_event_loop()
        self._parse_hosts()
        self._parse_nameserver()

    @lru_cache(seconds=300)
    def resolve(self, hostname):
        if hostname in self._hosts:
            return self._hosts[hostname]
        for server in self._servers:
            connection = self._loop.create_datagram_endpoint(
                lambda: DNSProtocol(hostname, QTYPE_AAAA),
                remote_addr=(str(server), 53)
            )
            transport, protocol = self._loop.run_until_complete(connection)

            self._loop.run_forever()
            transport.close()
            if protocol.result:
                self._loop.close()
                return protocol.result
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


if __name__ == '__main__':
    resolver = DNSResolver()
    print(resolver.resolve('www.baidu.com'))
