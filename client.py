import socket 
from datetime import datetime
from hashlib import md5
from struct import pack

SRC_PORT = 9999
DEST_PORT = 3030
HOST = 'localhost'


def UDP_packet(src_port, dest_port, data):
    return UDP_header(src_port, dest_port, data) + data.encode()

def UDP_header(src_port, dest_port, data):
    data_length = len(data)
    checksum = checksum_generator(data)
    header = pack("!III32s", src_port, dest_port, data_length, bytes(checksum, 'utf-8'))
    print("header length :",len(header))
    return header

def checksum_generator(data):
    return md5(data.encode()).hexdigest()


receiver_addr = (HOST, DEST_PORT)
while(True):

    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.bind((HOST, SRC_PORT))
    
    data =  input("> ")

    if data == "close":
        client.close()
        break
    else:
        packet = UDP_packet(SRC_PORT, DEST_PORT, data)

        print(datetime.now().strftime("%H:%M:%S") + " :: Sending " + data)
        # print(packet)
        client.sendto(packet, receiver_addr)

        data, addr = client.recvfrom(1024) # buffer size is 1024 bytes
        print(addr)
        print(data)

        client.close()


