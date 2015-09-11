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
import time, datetime
import mqttclient
import thread
import select

c = mqttclient.MQTTClient()
conns = []
dict_sock = {}
class Server(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass


class Socks5Handler(SocketServer.StreamRequestHandler):
    # is it OK?
    global c, dict_conn
    def handle_and_send(self, sock, data):
        # TODO ENCRYPTION
        bytes_sent = 0
        # print [ord(i) for i in data]
        # print len(data)
        data = bytearray(data)
        # print 'req:', data
        c.client.publish('c2s',data)


    def handle_tcp(self, sock, remote, localport, remoteAddr, remotePort):
            fdset = [sock]
            while 1:
                r, w, e = select.select(fdset, [], [])

                if sock in r:
                    data = sock.recv(2048)
                    if len(data) <= 0:
                        return
                    lpStr = str(hex(localport))[2:]
                    raStr = str(remoteAddr)
                    rpStr = str(hex(remotePort))[2:]

                    lpStr = '0' * (4 - len(lpStr)) + lpStr
                    rpStr = '0' * (4 - len(rpStr)) + rpStr
                    lenRaStr = str(hex(len(raStr)))[2:]
                    raStr = '0' * (2- len(lenRaStr)) + lenRaStr + raStr

                    data = lpStr + raStr  + rpStr + data
                    self.handle_and_send(remote, data)
                    '''
                    '''
                    dict_sock[localport] = sock
                    if localport not  in conns:
                        conns.append(localport)
            while 1:
                if localport not in conns:
                    time.sleep(0.1)
                    return
            return
            '''
            '''
            timeout = 60
            i = time.time() + 60
            while 1:
                if time.time()>i:
                    del dict_conn[localport]
                    conns.remove(localport)
                    break
                if localport in dict_conn.keys():
                    bytes_sent = 0
                    dataReply = dict_conn[localport]
                    while 1:
                        r = sock.send(dataReply[bytes_sent:])
                        if r < 0:
                            del dict_conn[localport]
                            break
                        bytes_sent += r
                        if bytes_sent == len(dataReply):
                            del dict_conn[localport]
                            break



    def handle(self):
        try:
            conn = self.connection
            rf = self.rfile
            # print 'connection from ', self.client_address

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
            elif atyp == 4:
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

                    # print 'Tcp connect to', addr, port
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
                    self.handle_tcp(conn, remote, self.client_address[1], addr, port)

        except socket.error, e:
            print 'socket error!', e

        pass
i = 0
def on_message(client, userdata, msg):
    '''
    when mqtt message comes
    do:
    handle the payload and form the socket payload
    set a socket
    send the payload via socket.
    '''
    try:
        payload = msg.payload

        localPort = int(payload[0:4], 16)
        remoteAddrLen = int(payload[4:6],16)
        remoteAddr = payload[6:6+remoteAddrLen]
        remotePort = int(payload[6+remoteAddrLen:10+remoteAddrLen],16)
        data = payload[10+remoteAddrLen:]
        print 'localport:',localPort,'len', len(payload),'connection', conns
        dataReply = data
        if dataReply == 'cometoend':
            conns.remove(localPort)
            # print 'end!'
            return
        bytes_sent = 0
        sock = dict_sock[localPort]
        global i
        i += 1
        # print 'sent' , i
        while 1:
            r = sock.send(dataReply[bytes_sent:])
            if r < 0:
                break
            bytes_sent += r
            if bytes_sent == len(dataReply):
                break
    except Exception,e:
        print e
        return


if __name__ == '__main__':
    server = Server(('', 8765), Socks5Handler)
    c.client.on_message = on_message
    c.client.subscribe('s2c')
    thread.start_new_thread(c.client.loop_forever,())
    server.serve_forever()

