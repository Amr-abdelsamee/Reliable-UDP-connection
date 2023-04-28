import socket
from datetime import datetime
from hashlib import md5
from struct import unpack
from http10 import http_response


PORT = 3030
HOST = 'localhost'
FILES = ["index.html", "main.html", "photo.jpg"]



def packet_info(packet):
    """_summary: used to unpack the packet and extract header info and sepparate the data from the header

    Args:
        packet (bytes): packet recieved from the client

    Returns:
        dictionary contains all the information in the packet and a boolean indicating whether the data was corrupted.
    """
    udp_header = unpack("!HHH32s", packet[:38])
    tcp_header = unpack("!HHHH6s", packet[38:52])
    request = packet[52:]
    print("---------\nudp header")
    print(udp_header)
    print("---------\ntcp header")
    print(tcp_header)
    print("---------\nhttp request")
    print(request)
    print("---------")
    correct_checksum = udp_header[3].decode()
    checksum = check_data(request, correct_checksum)
    return checksum, {
        'src_port':udp_header[0],
        'dest_port':udp_header[1],
        'length':udp_header[2],
        'correct_checksum':correct_checksum,
        'request':request.decode()
    }



def check_data(data, checksum):
    """_summary: used to check the data by getting the hash of the recieved data and 
    compare it with the recieved hash (hash of the original data)

    Args:
        data (str): recieved data
        checksum (str): recieved hash (hash of the original data)

    Returns:
        boolean: True if there is a match otherwise, false.
    """
    if md5(data).hexdigest() != checksum:
        return False
    else:
        return True



def extract_http(request):
    """_summary: used to get the file and the method then get the response 
    based on the existance of the file.

    Args:
        request (str): the request from the client

    Returns:
        response (str):the response to send back to the client
    """
    http_parsed = request.split(" ")
    method = http_parsed[0]
    file = http_parsed[1].replace("/", "")
    if method == "GET":
        if file in FILES:
            response = http_response(method, "200", "OK", data=file)
        else:
            response = http_response(method, "404", "Not Found")
    elif method == "POST":
        response = http_response(method, "200", "OK")
    return response












while(True):
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((HOST, PORT))
    print(datetime.now().strftime("%H:%M:%S") + " :: waiting for messages...")

    packet, addr = server.recvfrom(1024) # buffer size is 1024 bytes
    print("*** message from:",addr)

    checksum, packet_data = packet_info(packet)
    print(packet_data)

    response = ""
    if checksum:
        response = extract_http(packet_data['request'])
    else:
        response = "corrupted!"
    server.sendto(response.encode(), addr)
    print("\n\n")
    server.close()
