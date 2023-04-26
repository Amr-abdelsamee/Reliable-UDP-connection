import socket 
from datetime import datetime
from hashlib import md5
from struct import pack
from http10 import http_request


SRC_PORT = 9999
DEST_PORT = 3030
HOST = 'localhost'
receiver_addr = (HOST, DEST_PORT)

def UDP_packet(src_port, dest_port, data):
    return UDP_header(src_port, dest_port, data) + data.encode()



def UDP_header(src_port, dest_port, data):
    data_length = len(data)
    checksum = checksum_generator(data)
    header = pack("!III32s", src_port, dest_port, data_length, bytes(checksum, 'utf-8'))
    print("UDP header length :",len(header))
    return header



def checksum_generator(data):
    return md5(data.encode()).hexdigest()












while(True):

    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.bind((HOST, SRC_PORT))
    method = input("GET/POST: ")
    file_name =  input("file name: ")

    if method.upper() == "POST":
        info = input("data:")
        request = http_request(method.upper(), file_name, data=info)
    elif method.upper() == "GET":
        request = http_request(method.upper(), file_name)
    

    packet = UDP_packet(SRC_PORT, DEST_PORT, request)
    print(datetime.now().strftime("%H:%M:%S") + " :: Sending: \n" + request)
    # print(packet)
    client.sendto(packet, receiver_addr)
    
    data, addr = client.recvfrom(1024) # buffer size is 1024 bytes
    print("\n***" + datetime.now().strftime("%H:%M:%S") + " :: response from:",addr)
    print("*** response:\n",data.decode(),"\n\n")
    client.close()


