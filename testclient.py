import socket
from zlib import crc32
from ReliableUDP import *
from http10 import *

SRC_ADDR, SRC_PORT = "localhost", 8888
DEST_ADDR, DEST_PORT = "localhost", 9999
host = f"HOST:{DEST_PORT}"
user_agent = (
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1"
)

# SOCK_DGRAM is the socket type to use for UDP sockets
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((SRC_ADDR, SRC_PORT))
sock.settimeout(PACKET_LOSS_TIMEOUT)
client_connection = ClientConnectionInfo()

while True:
    method = input("GET/POST: ").upper()
    info = None
    if method == "POST":
        info = input("data:")
        file_name = ""
    elif method != "GET":
        print("Enter valid method")
        continue
    if method == "GET":
        file_name = input("file name: ")
    
    http_request = get_http_request(method, file_name, info, host, user_agent)
    client_connection.send_packets_buffer = get_packets(
        http_request, client_connection.num
    )
    print(client_connection.send_packets_buffer)


    while len(client_connection.send_packets_buffer):
        next_packet = client_connection.send_packets_buffer.pop(0)
        sock.sendto(next_packet, (DEST_ADDR, DEST_PORT))
        while True:
            try:

                packet, (addr, port) = sock.recvfrom(MAX_PACKET_SIZE)
                # check not corrupted
                header = unpack(PACK_FORMAT, packet[:HEADER_LENGTH])
                checksum = header[0]
                num = header[1]
                ack = header[2]
                fin = header[3]

                packet = (
                    pack(
                        PACK_FORMAT,
                        0,
                        header[1],
                        header[2],
                        header[3],
                        header[4],
                    )
                    + packet[HEADER_LENGTH:]
                )
                if crc32(packet) == checksum:
                    if num != client_connection.num or not ack or fin:
                        raise socket.timeout
                    client_connection.receive_data_buffer.append(packet)
                    client_connection.num = not client_connection.num
                    break
                else:
                    raise socket.timeout  # resend last packet
            except socket.timeout:
                sock.sendto(next_packet, (DEST_ADDR, DEST_PORT))
    
    next_packet = get_ack_packet(not client_connection.num)
    sock.sendto(next_packet, (DEST_ADDR, DEST_PORT))



    client_connection.receive_data_buffer = []
    more = 1
    while more:
        try:
            packet, (addr, port) = sock.recvfrom(MAX_PACKET_SIZE)
            # check not corrupted
            header = unpack(PACK_FORMAT, packet[:HEADER_LENGTH])
            checksum = header[0]
            num = header[1]
            fin = header[3]
            more = header[4]
            packet = (
                pack(
                    PACK_FORMAT,
                    0,
                    header[1],
                    header[2],
                    header[3],
                    header[4],
                )
                + packet[HEADER_LENGTH:]
            )
            if crc32(packet) == checksum:
                if num != client_connection.num or fin:
                    raise socket.timeout
                client_connection.receive_data_buffer.append(
                    packet[HEADER_LENGTH:].decode()
                )
                next_packet = get_ack_packet(client_connection.num)
                client_connection.num = not client_connection.num
                sock.sendto(next_packet, (DEST_ADDR, DEST_PORT))
                
            else:
                raise socket.timeout
        except socket.timeout:
            sock.sendto(next_packet, (DEST_ADDR, DEST_PORT))


    http_response = "".join(client_connection.receive_data_buffer)
    print("http response:: \n"+http_response)

