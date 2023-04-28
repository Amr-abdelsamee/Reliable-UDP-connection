import socket 
from datetime import datetime
from hashlib import md5
from struct import pack
from http10 import http_request


SRC_PORT = 9999
DEST_PORT = 3030
HOST = 'localhost'
receiver_addr = (HOST, DEST_PORT)

def packet(src_port, dest_port, data):
    UDP_header_ = UDP_header(src_port, dest_port, data)
    
    # TODO : function to split the data into packets => get Seq_num, Ack_num, Control_Flag_Bits
    
    TCP_header_ = TCP_header(Seq_num=1, Ack_num=1, Control_Flag_Bits="000000")
    print(len(TCP_header_))
    data = data.encode()
    return UDP_header_ + TCP_header_ + data



def UDP_header(src_port, dest_port, data):
    length = len(data) + 14 + 38 # length of the  data + length of the TCP header + length of the UDP header
    checksum = checksum_generator(data)
    header = pack("!HHH32s", src_port, dest_port, length, bytes(checksum, 'utf-8'))
    return header



def checksum_generator(data):
    return md5(data.encode()).hexdigest()


def TCP_header(Seq_num, Ack_num, Control_Flag_Bits):

    # Control_Flag_Bits = "000000"
    length = 14
    window_size = 0
    return pack("!HHHH6s", Seq_num, Ack_num, length, window_size, bytes(Control_Flag_Bits, 'utf-8'))










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
    

    packet = packet(SRC_PORT, DEST_PORT, request)
    print(datetime.now().strftime("%H:%M:%S") + " :: Sending: \n" + request)
    # print(packet)
    client.sendto(packet, receiver_addr)
    
    data, addr = client.recvfrom(1024) # buffer size is 1024 bytes
    print("\n***" + datetime.now().strftime("%H:%M:%S") + " :: response from:",addr)
    print("*** response:\n",data.decode(),"\n\n")
    client.close()





