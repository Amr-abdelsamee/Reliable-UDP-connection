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
    elif method != "GET":
        print("Enter valid method")
    file_name = input("file name: ")

    if method == "POST":
        http_request = get_http_request(method, file_name, info, host, user_agent)
        reliable_udp_packets = get_packets(
            SRC_PORT, http_request, client_connection.num
        )

        while len(reliable_udp_packets):
            next_packet = reliable_udp_packets.pop(0)
            sock.sendto(next_packet, (DEST_ADDR, SRC_PORT))
            while True:
                try:
                    packet = str(sock.recvfrom(MAX_PACKET_SIZE), "utf-8")
                    # check not corrupted
                    header = unpack(packet[:HEADER_LENGTH])
                    checksum = header[0]
                    num = header[2]
                    ack = header[3]
                    fin = header[4]
                    packet = (
                        pack(
                            PACK_FORMAT,
                            0,
                            header[1],
                            header[2],
                            header[3],
                            header[4],
                            header[5],
                        )
                        + packet[HEADER_LENGTH:]
                    )
                    if crc32(packet) == checksum:
                        if num != client_connection.num or not ack or fin:
                            raise socket.timeout
                        client_connection.num = not client_connection.num
                    else:
                        raise socket.timeout  # resend last packet
                except socket.timeout:
                    sock.sendto(next_packet, (DEST_ADDR, DEST_PORT))

        client_connection.data_buffer = []
        more = 1
        while more:
            try:
                packet = str(sock.recvfrom(MAX_PACKET_SIZE), "utf-8")
                # check not corrupted
                header = unpack(packet[:HEADER_LENGTH])
                checksum = header[0]
                num = header[2]
                fin = header[4]
                more = header[5]
                packet = (
                    pack(
                        PACK_FORMAT,
                        0,
                        header[1],
                        header[2],
                        header[3],
                        header[4],
                        header[5],
                    )
                    + packet[HEADER_LENGTH:]
                )
                if crc32(packet) == checksum:
                    if num != client_connection.num or fin:
                        raise socket.timeout
                    client_connection.data_buffer.append(
                        packet[HEADER_LENGTH:].decode()
                    )
                    client_connection.num = not client_connection.num
                    response_packet = get_ack_packet(SRC_PORT, client_connection.num)
                    sock.sendto(response_packet, (DEST_ADDR, DEST_PORT))
                else:
                    raise socket.timeout
            except socket.timeout:
                pass
    else:
        while len(reliable_udp_packets):
            next_packet = reliable_udp_packets.pop(0)
            sock.sendto(next_packet, (DEST_ADDR, SRC_PORT))
            while True:
                try:
                    packet = str(sock.recvfrom(MAX_PACKET_SIZE), "utf-8")
                    # check not corrupted
                    header = unpack(packet[:HEADER_LENGTH])
                    checksum = header[0]
                    num = header[2]
                    ack = header[3]
                    fin = header[4]
                    packet = (
                        pack(
                            PACK_FORMAT,
                            0,
                            header[1],
                            header[2],
                            header[3],
                            header[4],
                            header[5],
                        )
                        + packet[HEADER_LENGTH:]
                    )
                    if crc32(packet) == checksum:
                        if num != client_connection.num or not ack or fin:
                            raise socket.timeout
                        client_connection.num = not client_connection.num
                    else:
                        raise socket.timeout  # resend last packet
                except socket.timeout:
                    sock.sendto(next_packet, (DEST_ADDR, DEST_PORT))

        client_connection.data_buffer = []
        more = 1
        while more:
            try:
                packet = str(sock.recvfrom(MAX_PACKET_SIZE), "utf-8")

                header = unpack(packet[:HEADER_LENGTH])

                checksum = header[0]
                num = header[2]
                fin = header[4]
                more = header[5]

                packet = (
                    pack(
                        PACK_FORMAT,
                        0,
                        header[1],
                        header[2],
                        header[3],
                        header[4],
                        header[5],
                    )
                    + packet[HEADER_LENGTH:]
                )
                if crc32(packet) == checksum:
                    if num != client_connection.num or fin:
                        raise socket.timeout
                    client_connection.data_buffer.append(
                        packet[HEADER_LENGTH:].decode()
                    )
                    client_connection.num = not client_connection.num
                    response_packet = get_ack_packet(SRC_PORT, client_connection.num)
                    sock.sendto(response_packet, (DEST_ADDR, DEST_PORT))
                else:
                    raise socket.timeout
            except socket.timeout:
                sock.sendto(packet, (DEST_ADDR, DEST_PORT))

    http_response = ""
    for data in client_connection.data_buffer:
        http_response += data

    # parse http_response or something
    print(http_response)
