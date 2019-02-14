from network import LoRa
import socket
import machine
import pycom
import time
import struct
import os
from uos import urandom
from machine import Pin
from dth import DTH

# A basic package header
# B: 1 byte for the deviceId
# B: 1 byte for the pkg size
# B: 1 byte for the messageId
# %ds: Formatted string for string
_LORA_PKG_FORMAT = "!BBB%ds"

# A basic ack package
# B: 1 byte for the deviceId
# B: 1 byte for the pkg size
# B: 1 byte for the messageId
# B: 1 byte for the Ok (200) or error messages
_LORA_PKG_ACK_FORMAT = "BBBB"

# This device ID, use different device id for each device
_DEVICE_ID = 0x01
_MAX_ACK_TIME = 5000
_RETRY_COUNT = 3


""" ========== METHODS OF MAIN PROGRAM ========== """

# Method for reading the sensor
def read_sensor():
    pycom.heartbeat(False)
    pycom.rgbled(0x000f00) # green = reading
    th = DTH(Pin('P3', mode=Pin.OPEN_DRAIN),0) # P3 = G24
    time.sleep(1)
    result = th.read()
    if result.is_valid():
        return result

# Method to increase message id and keep in between 1 and 255
msg_id = 0
def increase_msg_id():
    global msg_id
    msg_id = (msg_id + 1) & 0xFF

# Method for acknowledge waiting time keep
def check_ack_time(from_time):
    current_time = time.ticks_ms()
    return (current_time - from_time > _MAX_ACK_TIME)

# Method to send messages
def send_msg(msg):
    global msg_id
    retry = _RETRY_COUNT

    while(retry > 0 and not retry == -1):
        retry -= 1
        pkg = struct.pack(_LORA_PKG_FORMAT % len(msg), _DEVICE_ID, len(msg), msg_id, msg)
        lora_sock.send(pkg)

        # Wait for the response from the server
        start_time = time.ticks_ms()

        while(not check_ack_time(start_time)):
            recv_ack = lora_sock.recv(256)
            # If a message of the size of the ackowledge message is received
            if(len(recv_ack) == 4):
                device_id, pkg_len, recv_msg_id, status = struct.unpack(_LORA_PKG_ACK_FORMAT, recv_ack)
                if(device_id == _DEVICE_ID and recv_msg_id == msg_id):
                    if(status == 200):
                        return True
                    else:
                        return False
        time.sleep_ms(urandom(1)[0] << 2)
    return False

""" ========== MAIN PROGRAM ========== """

#LoRa setup

# Open a Lora Socket, use tx_iq to avoid listening to our own messages
lora = LoRa(mode=LoRa.LORA, tx_iq=True)
lora_sock = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
lora_sock.setblocking(False)

while (True):

    result = read_sensor()
    temp = result.temperature
    hum = result.humidity
    data_to_send = str(temp) + "|" + str(hum)
    success = send_msg(data_to_send)

    pycom.rgbled(0x00000f) # blue = sent
    time.sleep(1)

    if(success):
        print("ACK RECEIVED: %d" % msg_id)
        increase_msg_id()
    else:
        print("MESSAGE FAILED")
