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

i = 0
# callback of coming message
def on_message(client, userdata, msg):
    payload = msg.payload
    print payload



if __name__ == '__main__':
    server = mqttclient.MQTTClient()
    server.client.on_message = on_message
    server.client.subscribe('s2c')
    for i in range(2000):
        server.client.publish('c2s',bytearray(str(i)),qos=1)
    server.client.loop_forever()

