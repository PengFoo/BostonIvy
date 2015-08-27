# !/usr/bin/python
# -*- coding: UTF-8 -*-

__author__ = 'fp'

import socket


# socks5 rfc 1928 at http://www.openssh.com/txt/rfc1928.txt
# socks5 rfc 1928 chinese version at http://blog.chinaunix.net/uid-26548237-id-3434356.html


def client():
    server = '127.0.0.1'
    port = 7654
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # establish socket
    s.connect((server, port))

    '''
    The client connects to the server, and sends a version
    identifier/method selection message:

        +----+----------+----------+
        |VER | NMETHODS | METHODS  |
        +----+----------+----------+
        | 1  |    1     | 1 to 255 |
        +----+----------+----------+

    The VER field is set to X'05' for this version of the protocol.  The
    NMETHODS field contains the number of method identifier octets that
    appear in the METHODS field.
    '''
    # sent sokcs5 header
    # ver = 0x05, nmethods = 0x01, methods = 0x00
    s.sendall('\x05\x01\x00')

    print repr(s.recv(1024))

    '''
     The SOCKS request is formed as follows:

        +----+-----+-------+------+----------+----------+
        |VER | CMD |  RSV  | ATYP | DST.ADDR | DST.PORT |
        +----+-----+-------+------+----------+----------+
        | 1  |  1  | X'00' |  1   | Variable |    2     |
        +----+-----+-------+------+----------+----------+

     Where:

          o  VER    protocol version: X'05'
          o  CMD
             o  CONNECT X'01'
             o  BIND X'02'
             o  UDP ASSOCIATE X'03'
          o  RSV    RESERVED
          o  ATYP   address type of following address
             o  IP V4 address: X'01'
             o  DOMAINNAME: X'03'
             o  IP V6 address: X'04'
          o  DST.ADDR       desired destination address
          o  DST.PORT desired destination port in network octet
             order

    '''
    # send request header
    # ver = 0x05, cmd = 0x01, rsv = 0x00, atvp = 0x01,
    # dst.addr = 0x7f.0x00.0x00.0x01 (127.0.0.1), dst.port =0x50 (80)
    #
    # addr and port currently unused
    #
    s.sendall("\x05\x01\x00\x01\x7f\x00\x00\x01\x00\x50")
    print repr(s.recv(1024))

    # http request
    s.sendall("this is a request via socks5:)")
    print repr(s.recv(1024))

if __name__ == '__main__':
    client()