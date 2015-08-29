# !/usr/bin/python
# -*- coding: UTF-8 -*-
__author__ = 'fp'

'''
local.py is actually a socks5 server to send data
to remote server via MQTT protocal
'''

import socket
import sys
import select
import SocketServer
import struct
import time
import mqttclient


class Server(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass


class Socks5Handler(SocketServer.StreamRequestHandler):
    c = mqttclient.MQTTClient()
    def handle_and_send(self, sock, data):
        # TODO ENCRYPTION
        # TODO SEND VIA MQTT
        bytes_sent = 0
        # print [ord(i) for i in data]
        # print len(data)
        data = bytearray(data)
        self.c.client.publish('c2s',data)

    def handle_tcp(self, sock, remote):
        fdset = [sock, remote]
        while True:
            r, w, e = select.select(fdset, [], [])

            if sock in r:
                data = sock.recv(4096)
                if len(data) <= 0:
                    break
                self.handle_and_send(remote, data)

            if remote in r:
                data = remote.recv(4096)
                if len(data) <= 0:
                    break
                self.handle_and_send(sock, data)

    def handle(self):
        try:
            conn = self.connection
            rf = self.rfile
            print 'connection from ', self.client_address
            # version 0x05, method 0x00, see socks5client and socks5 server for socks5 more info

            # should be client socks5 header 0x05 0x00 0x01
            rf.read(3)  # or conn.recv(1024)
            conn.send(b'\x05\x00')

            data = rf.read(4)

            # socks version, 0x05 for socks v5
            ver = ord(data[0])

            # cmd
            # 0x01 for connect
            # 0x02 for bind
            # 0x03 for udp associate
            cmd = ord(data[1])

            # rsv no use
            rsv = ord(data[2])

            # address type
            # 0x01 for ipv4 addr
            # 0x03 for domainname
            # 0x04 for ipv6 addr
            atyp = ord(data[3])

            # print ver,cmd,rsv,atyp
            addr = 0
            if atyp == 1:
                # ipv4, next 4 bytes shall be the ip addr
                addr = socket.inet_ntoa(rf.read(4))
                # print addr
            elif atyp == 3:
                # domainname
                # first byte for the length of domain, no \0 character
                length = ord(rf.read(1))
                addr = rf.read(length)
                # print addr
            elif ayyp == 4:
                # ipv6
                # TODO handle the ipv6 address
                addr = 0
                pass
            port = struct.unpack('>H', rf.read(2))[0]

            # reply ver, rep, rsv, atyp, wait to add other info
            reply = '\x05\x00\x00\x01'

            remote = None
            # start connection to remote server
            try:
                if cmd == 1:
                    # tcp connect
                    # TODO REPLACE THE SOCKET CODE TO THE MQTT CODE
                    remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    remote.connect((addr, port))
                    print 'Tcp connect to', addr, port
                else:
                    # Command not supported
                    reply = b"\x05\x07\x00\x01"
                local = remote.getsockname()
                reply += socket.inet_aton(local[0]) + struct.pack(">H", local[1])
            except Exception, e:
                # connection refused
                reply = '\x05\x05\x00\x01\x00\x00\x00\x00\x00\x00'
                print e

            conn.send(reply)
            # 3. Transfering
            if reply[1] == '\x00':  # Success
                if cmd == 1:    # 1. Tcp connect
                    self.handle_tcp(conn, remote)

        except socket.error, e:
            print 'socket error!', e

        pass


server = Server(('', 8765), Socks5Handler)
server.serve_forever()