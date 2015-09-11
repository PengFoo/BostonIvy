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
import gc


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
        # print tmp
        if tmp == '\r':
            tmp += socket.recv(1)
            # print tmp
            line += tmp
            if tmp == '\r\n':
                header.append(line)
                line = ''
                tmp = socket.recv(2)
                # print tmp
                line += tmp
                if tmp == '\r\n':
                    header.append(line)
                    length = getLength(header)
                    # print length
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
    # print '\n'.join(header)
    for line in header:
        if line == '\r\n':
            continue
        #print line
        # value has a space in the front
        line = line[:-2]
        if 'HTTP/1.' in line:
            # Any response message which "MUST NOT" include a message-body
            # (such as the 1xx, 204, and 304 responses and any response to a HEAD request)
            # is always terminated by the first empty line after the header fields, regardless
            # of the entity-header fields present in the message.
            if line.split()[1] == '304' or line.split()[1] == '204' or line.split()[1][0]=='1':
                return 0
        else:

            key,value = line.split(':')[0],line.split(':')[1][1:]
            #print key,value
            h[key] = value
    #print h
    if 'Transfer-Encoding' in h.keys() and h['Transfer-Encoding'] == 'chunked':
        # chunked
        return -1
    elif 'Content-Length'in h.keys():
        # content-length
        # print h['Content-Length']
        return int(h['Content-Length'])
    return length

def recvBySize(socket, size, buff):
    data = ''
    _size = size
    while size >= buff:
        data += socket.recv(buff)
        size -= buff
    data += socket.recv(size)
    while len(data) < _size:
        data += socket.recv(_size-len(data))

    return data

# @profile
def recv(the_socket, header, client):
    data=''
    contentLength = 0
    t1 = time.time()
    headerStr,length = getHeaderAndLength(the_socket)

    data = headerStr
    client.publish('s2c',bytearray(header+data))
    data = ''
    t2 = time.time()
    # print 'get header and length using' , str(t2-t1)
    # 1024 per message
    # print length
    # print headerStr
    length = - 100
    if length > 0:
        while length > 2048:
            data += the_socket.recv(2048)
            client.publish('s2c',bytearray(header+data))
            data = ''
            length -= 2048
        t1 = time.time()
        data += the_socket.recv(length)
        t2 = time.time()
        client.publish('s2c',bytearray(header+data))

    elif length == -2:
        _len = 0
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
                        client.publish('s2c',bytearray(header+data))
                        _len = 0
                        break
            _len += 1
            if _len >= 2048:
                client.publish('s2c',bytearray(header+data))
                data = ''
                _len = 0
    elif length == -1:
        # TODO support chunk with format, now just support chunk with size
        # chunked
        # chunk -->
        # (size)\r\n(data of size)\r\n

        '''
        while 1:
            data = the_socket.recv(3)
            while data[-2:] != '\r\n':
                data += the_socket.recv(1)
                if len(data)>1024:
                    pass

            #print len(data)
            #print [hex(ord(i)) for i in data]
            if data == '0\r\n':
                client.publish('s2c',bytearray(header+data))
                return

        '''
        while 1:
            # the smallest chunk is 3 bytes :
            # 0\r\n
            data = the_socket.recv(3)

            # recv till got the \r\n
            while data[-2:] != '\r\n':
                data += the_socket.recv(1)
            _len = len(data)

            # chunk size
            size = int(data[:-2],16)

            # chunk size == 0 means last chunk
            if size  == 0:
                data = '0' +  the_socket.recv(2)
                print 'end!', [hex(ord(i)) for i in data]
                client.publish('s2c',bytearray(header+data))
                break



            data += recvBySize(the_socket, size, 1024)

            print len(data),size+ _len

            data += the_socket.recv(2) # \r\n
            client.publish('s2c',bytearray(header+data))
            # print [hex(ord(i)) for i in data]


            # print size


    elif length == 0:
        client.publish('s2c',bytearray(header+data))
    else:
        while True:
            data = the_socket.recv(2048)
            if len(data) <= 0:
                break
            client.publish('s2c',bytearray(header+data))
            print 'published!'

    return

sentnum = 0
def reply(client,payload):

    global  sentnum
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
    # remote.setblocking(0)
    fdset = [remote]
    while 1:
        r, w, e = select.select(fdset, [], [])
        if remote in r:
            data = remote.recv(4096)
            if len(data) <= 0:
                client.publish('s2c',header + 'cometoend')
                sentnum += 1
                # print 'send an end!',sentnum
                break
            print 'len:',len(header+data),'no.',sentnum
            sentnum += 1
            client.publish('s2c',bytearray(header+data))

            # print 'send',sentnum

    return


if __name__ == '__main__':

    server = mqttclient.MQTTClient()
    server.client.on_message = on_message
    server.client.subscribe('c2s')
    t = time.time() + 90
    while 1:
        '''
        if time.time() > t:
            break
        '''
        server.client.loop()

