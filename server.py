import socket
from datetime import datetime
from hashlib import md5
from struct import unpack

PORT = 3030
HOST = 'localhost'


def packet_info(packet):
    udp_header = unpack("!III32s", packet[:44])
    data = packet[44:]
    correct_checksum = udp_header[3].decode()
    checksum = check_data(data, correct_checksum)
    return {
        'src_port':udp_header[0],
        'dest_port':udp_header[1],
        'length':udp_header[2],
        'correct_checksum':correct_checksum,
        'data':data,
        'checksum':checksum
    }

def check_data(data, checksum):
    if md5(data).hexdigest() != checksum:
        return False
    else:
        return True



while(True):
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((HOST, PORT))
    print(datetime.now().strftime("%H:%M:%S") + " :: waiting for messages...")

    packet, addr = server.recvfrom(1024) # buffer size is 1024 bytes
    print(addr)

    packet_data = packet_info(packet)
    print(packet_data)
    response = ""
    if packet_data['checksum']:
        response = "correct!"
    else:
        response = "corrupted!"
    server.sendto((response.upper()).encode(), addr)

    server.close()
