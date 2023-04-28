import socket
import sys
from zlib import crc32
from ReliableUDP import ClientConnectionInfo, ReliableUDPClient

HOST, PORT = "localhost", 9999
host = f"HOST:{PORT}"
user_agent = (
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1"
)

# SOCK_DGRAM is the socket type to use for UDP sockets
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
reliable_udp_client = ReliableUDPClient()
# As you can see, there is no connect() call; UDP has no connections.
# Instead, data is directly sent to the recipient via sendto().

while True:
    method = input("GET/POST: ")
    info = None
    if method.upper() == "POST":
        info = input("data:")
    elif method.upper() != "GET":
        print("Enter valid method")
    file_name = input("file name: ")

    http_request = reliable_udp_client.wrap_http(file_name, info, host, user_agent)
    reliable_udp_packets = reliable_udp_client.get_packets(http_request)

    while True:
        window_packets = reliable_udp_packets[:4]
        for packet in window_packets:
            sock.sendto(bytes(packet, "utf-8"), (HOST, PORT))
        sock.settimeout(reliable_udp_client.packet_loss_timeout)

        received_all = False

        while not received_all:
            try:
                received = str(sock.recv(reliable_udp_client.max_packet_size), "utf-8")
                reliable_udp_client.client_connection.packets_buffer.append(received)
            except socket.timeout:
                break
            # check if flag indicates there's another packet incoming (message larger than packet length)
            received_all = True

    file_name = input("file name: ")
    # sock.sendto(bytes(data + "\n", "utf-8"), (HOST, PORT))
    received = str(sock.recv(1024), "utf-8")

    # print("Sent:     {}".format(data))
    print("Received: {}".format(received))
