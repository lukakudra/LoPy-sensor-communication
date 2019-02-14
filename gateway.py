import socket
import struct
from network import LoRa
import time
import pycom

# A basic package header
# B: 1 byte for the deviceId
# B: 1 byte for the pkg size
# B: 1 byte for the messageId
# %ds: Formated string for string
_LORA_PKG_FORMAT = "!BBB%ds"

# A basic ack package
# B: 1 byte for the deviceId
# B: 1 byte for the pkg size
# B: 1 byte for the messageId
# B: 1 byte for the Ok (200) or error messages
_LORA_PKG_ACK_FORMAT = "BBBB"

# Open a Lora Socket, use rx_iq to avoid listening to our own messages
lora = LoRa(mode=LoRa.LORA, rx_iq=True)
lora_sock = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
lora_sock.setblocking(False)

data = {} # dictionary for handling messages

pycom.heartbeat(True) # heartbeat marks the gateway

while (True):
    # Since the maximum body size in the protocol is 255 the request is limited to 512 bytes
    recv_pkg = lora_sock.recv(512)

    # If at least a message with the header is received process it
    if (len(recv_pkg) > 3):
        recv_pkg_len = recv_pkg[1]

        # If message is corrupted should not continue processing
        if (not len(recv_pkg) == recv_pkg_len + 3):
            continue

        # Unpack the message based on the protocol definition
        device_id, pkg_len, msg_id, msg = struct.unpack(_LORA_PKG_FORMAT % recv_pkg_len, recv_pkg)

        if device_id == 1:
            data["dht"] = msg.decode('UTF-8')
        elif device_id == 2:
            data["foto"] = msg.decode('UTF-8')

        # Respond to the device with an acknowledge package
        time.sleep(1)
        ack_pkg = struct.pack(_LORA_PKG_ACK_FORMAT, device_id, 1, msg_id, 200)
        lora_sock.send(ack_pkg)

        if "dht" in data and "foto" in data:

            datalist = data.get("dht").split("|")
            temp = int(datalist[0])
            hum = int(datalist[1])
            light = int(data.get("foto"))

            print("CURRENT CONDITIONS:")
            if light < 1000:
                print("The area is dark! Sensor reading: %d" % light)
            elif light >= 1000:
                print("The area is filled with light! Sensor reading: %d" % light)
            print("Temperature: %d C" % temp)
            print("Humidity: %d %%\n" % hum)
