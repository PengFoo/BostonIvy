# !/usr/bin/python
# -*- coding: UTF-8 -*-

__author__ = 'fp'

import socket


# socks5 rfc 1928 at http://www.openssh.com/txt/rfc1928.txt
# socks5 rfc 1928 chinese version at http://blog.chinaunix.net/uid-26548237-id-3434356.html


def server():
    HOST = '0.0.0.0'
    PORT = 7654
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(1024)
    conn, addr = s.accept()
    print repr(conn.recv(1024))

    '''
    The server selects from one of the methods given in METHODS, and
    sends a METHOD selection message:

                         +----+--------+
                         |VER | METHOD |
                         +----+--------+
                         | 1  |   1    |
                         +----+--------+

    If the selected METHOD is X'FF', none of the methods listed by the
    client are acceptable, and the client MUST close the connection.

    The values currently defined for METHOD are:

          o  X'00' NO AUTHENTICATION REQUIRED
          o  X'01' GSSAPI
          o  X'02' USERNAME/PASSWORD
          o  X'03' to X'7F' IANA ASSIGNED
          o  X'80' to X'FE' RESERVED FOR PRIVATE METHODS
          o  X'FF' NO ACCEPTABLE METHODS

    The client and server then enter a method-specific sub-negotiation.
    '''
    conn.send("\x05\x00")
    print repr(conn.recv(1024))

    '''
        The SOCKS request information is sent by the client as soon as it has
    established a connection to the SOCKS server, and completed the
    authentication negotiations.  The server evaluates the request, and
    returns a reply formed as follows:

        +----+-----+-------+------+----------+----------+
        |VER | REP |  RSV  | ATYP | BND.ADDR | BND.PORT |
        +----+-----+-------+------+----------+----------+
        | 1  |  1  | X'00' |  1   | Variable |    2     |
        +----+-----+-------+------+----------+----------+

     Where:

          o  VER    protocol version: X'05'
          o  REP    Reply field:
             o  X'00' succeeded
             o  X'01' general SOCKS server failure
             o  X'02' connection not allowed by ruleset
             o  X'03' Network unreachable
             o  X'04' Host unreachable
             o  X'05' Connection refused
             o  X'06' TTL expired
             o  X'07' Command not supported
             o  X'08' Address type not supported
             o  X'09' to X'FF' unassigned
          o  RSV    RESERVED
          o  ATYP   address type of following address
    '''

    # ver=5, Reply=0(succeeded), reserved=0, atype=1(ip), host=127.0.0.1 + port=80
    #
    # host and port currently unused
    #
    conn.send("\x05\x00\x00" + "\x01\x7f\x00\x00\x01" + "\x00\x50")

    # http-request from client
    x = conn.recv(4096)
    print x

    # http-response
    conn.send("this is a response via socks5:)")

if __name__ == '__main__':
    server()