import socket
from zlib import crc32
from ReliableUDP import *

HOST, PORT = "localhost", 9999
host = f"HOST:{PORT}"
user_agent = (
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1"
)

# SOCK_DGRAM is the socket type to use for UDP sockets
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_connection = ClientConnectionInfo()

while True:
    method = input("GET/POST: ")
    info = None
    if method.upper() == "POST":
        info = input("data:")
    elif method.upper() != "GET":
        print("Enter valid method")
    file_name = input("file name: ")

    http_request = wrap_http(file_name, info, host, user_agent)
    reliable_udp_packets = get_packets(PORT, http_request, client_connection.num)

    while len(reliable_udp_packets):
        next_packet = reliable_udp_packets[0]
        reliable_udp_packets = reliable_udp_packets[1:]
        sock.sendto(bytes(next_packet, "utf-8"), (HOST, PORT))
        sock.settimeout(PACKET_LOSS_TIMEOUT)

        while True:
            try:
                packet = str(sock.recvfrom(MAX_PACKET_SIZE), "utf-8")
                # check not corrupted
                header = unpack(packet[:HEADER_LENGTH])
                checksum = header[0]
                header[0] = 0
                packet = (
                    pack(
                        PACK_FORMAT,
                        header[0],
                        header[1],
                        header[2],
                        header[3],
                        header[4],
                        header[5],
                    )
                    + packet[HEADER_LENGTH:]
                )
                if crc32(packet) == checksum:
                    # TODO: implement receiving or sending files
                    client_connection.packets_buffer.append(packet)
                else:
                    raise socket.timeout
            except socket.timeout:
                sock.sendto(bytes(next_packet, "utf-8"), (HOST, PORT))
