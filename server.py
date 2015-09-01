# !/usr/bin/python
# -*- coding: UTF-8 -*-

__author__ = 'fp'

'''
subscribe the topic,
when message received,
handle the message, get 1.local port 2.remote ip 3.remote port
2 and 3 make a socket from the server to the website
127.0.0.1 and 1 make a socket from local to the browser
between the server and local, use the MQTT protocol v3.1
'''

import socket
import sys
import select
import SocketServer
import struct
import time
import mqttclient
import threadpool
import datetime


pool = threadpool.ThreadPool(300)
i = 0
# callback of coming message
def on_message(client, userdata, msg):
    payload = msg.payload
    # print payload
    req = threadpool.WorkRequest(reply,[client, payload])
    pool.putRequest(req)

def getHeaderAndLength(socket):
    header = []
    line = ''
    length = 0
    while 1:
        tmp = socket.recv(1)
        if tmp == '\r':
            tmp += socket.recv(1)
            line += tmp
            if tmp == '\r\n':
                header.append(line)
                line = ''
                tmp = socket.recv(2)
                line += tmp
                if tmp == '\r\n':
                    header.append(line)
                    length = getLength(header)
                    break
                else:
                    continue
            else:
                continue
        else:
            line += tmp
            continue

    return ''.join(header),length

'''
according to afc 2616
chapter 4.4 :: message length
http://www.w3.org/Protocols/rfc2616/rfc2616.html
'''
# need socket param because if the head is chunked,
# need recv more data to decide the length
def getLength(header):
    length = -2
    h = {}
    for line in header:
        # value has a space in the front
        if 'HTTP/1.' in line:
            # Any response message which "MUST NOT" include a message-body
            # (such as the 1xx, 204, and 304 responses and any response to a HEAD request)
            # is always terminated by the first empty line after the header fields, regardless
            # of the entity-header fields present in the message.
            if line.split()[1] == '304' or line.split()[1] == '204' or line.split()[1][0]=='1':
                return 0
        key,value = line.split(':')[0],line.split(':')[1][1:]
        h[key] = value
    if 'Transfer-Encoding' in h.keys() and h['Transfer-Encoding'] == 'chunked':
        # chunked
        return -1
    elif 'Content-Length'in h.keys():
        # content-length
        return int(h['Content-Length'])
    return length


def recv(the_socket, header, client):
    data=''
    contentLength = 0
    headerStr,length = getHeaderAndLength(the_socket)
    dataSent = 0
    # 1024 per message

    if length > 0:
        while length > 1024:
            data = headerStr + the_socket.recv(length)
    elif length == -1 or length == -2:
        data = headerStr
        while 1:
            tmp = the_socket.recv(1)
            data += tmp
            if tmp == '\r':
                tmp = the_socket.recv(1)
                data += tmp
                if tmp == '\n':
                    tmp = the_socket.recv(2)
                    data += tmp
                    if tmp == '\r\n':
                        break
    elif length == 0:
        data = headerStr

    while True:

        # t1 = datetime.datetime.now()
        data = the_socket.recv(length)
        # t2 = datetime.datetime.now()
        print data
        #print 'using ', str((t2 - t1).seconds)+'.'+str((t2-t1).microseconds), 's get receive 1024'
        if not data: break
        client.publish('s2c',bytearray(header+data))
    return

def receive(sock, EOFChar=chr(255)):
    msg = ''
    MSGLEN = 100
    while len(msg) < MSGLEN:
      chunk = sock.recv(MSGLEN-len(msg))
      if chunk.find(EOFChar) != -1:
        msg = msg + chunk
        return msg

      msg = msg + chunk
      return msg

def reply(client,payload):
    localPort = int(payload[0:4], 16)
    remoteAddrLen = int(payload[4:6],16)
    remoteAddr = payload[6:6+remoteAddrLen]
    remotePort = int(payload[6+remoteAddrLen:10+remoteAddrLen],16)
    header = payload[:10+remoteAddrLen]
    data = payload[10+remoteAddrLen:]
    remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote.connect((remoteAddr, remotePort))
    err = remote.sendall(data)
    t1 = datetime.datetime.now()
    # data2reply = recv_basic(remote)
    data2reply = recv(remote, header, client)
    t2 = datetime.datetime.now()
    # print 'using ', str((t2 - t1).seconds)+'.'+str((t2-t1).microseconds), 's get receive from:' , remoteAddr
    # client.publish('s2c',bytearray(header+data2reply))
    # i = 1
    # while 1:
    #     response = remote.recv()
    #     if not response:
    #         break
    #     else:
    #         i+=1
    #         print i
    #         data2reply += response
    #         print 'data get', data2reply
    #
    #

    return


if __name__ == '__main__':

    server = mqttclient.MQTTClient()
    server.client.on_message = on_message
    server.client.subscribe('c2s')
    while 1:

        server.client.loop()

