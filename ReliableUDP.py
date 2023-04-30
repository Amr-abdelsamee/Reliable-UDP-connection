import socket
from struct import pack, unpack
from zlib import crc32
from math import ceil
from http10 import get_http_response
from random import random

"""
Use RDT 3.0 for reliable data transfer over UDP
"""
MAX_PACKET_SIZE = 1024
PACKET_LOSS_TIMEOUT = 0.3
# 4 byte unsigned int [checksum, src_port], 1 byte bool [num, ACK, FIN, MORE]
PACK_FORMAT = "!I????"
HEADER_LENGTH = 8


class ClientConnectionInfo:
    num: bool = 0  # refer to the number of packet 0 or 1
    send_packets_buffer: list[str] = []
    receive_data_buffer: list[str] = []


class ReliableUDPServer:
    def serve_forever(self, packet_loss, error_rate):
        SRC_ADDR, SRC_PORT = "localhost", 9999
        server = "apache 2.0"
        # SOCK_DGRAM is the socket type to use for UDP sockets
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((SRC_ADDR, SRC_PORT))
        client_connection = ClientConnectionInfo()

        while True:
            client_connection.num = 0
            client_connection.receive_data_buffer = []
            sock.settimeout(None)
            print("Server start...")
            packet, (DEST_ADDR, DEST_PORT) = sock.recvfrom(MAX_PACKET_SIZE)
            header = unpack(PACK_FORMAT, packet[:HEADER_LENGTH])
            checksum = header[0]
            num = header[1]
            ack = header[2]
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
            if (
                crc32(packet) == checksum
                and num == client_connection.num
                and not ack
                and not fin
            ):
                client_connection.receive_data_buffer.append(
                    packet[HEADER_LENGTH:].decode()
                )
                sock.settimeout(PACKET_LOSS_TIMEOUT)
                more = 1
                while more:
                    try:
                        next_packet = get_ack_packet(client_connection.num)
                        send(
                            sock,
                            next_packet,
                            DEST_ADDR,
                            DEST_PORT,
                            packet_loss,
                            error_rate,
                        )
                        packet, (DEST_ADDR, DEST_PORT) = sock.recvfrom(MAX_PACKET_SIZE)
                        header = unpack(PACK_FORMAT, packet[:HEADER_LENGTH])
                        checksum = header[0]
                        num = header[1]
                        ack = header[2]
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
                        if (
                            crc32(packet) != checksum
                            or num != client_connection.num
                            or fin
                        ):
                            raise socket.timeout
                        elif ack:
                            client_connection.num = not client_connection.num
                        else:
                            client_connection.receive_data_buffer.append(
                                packet[HEADER_LENGTH:].decode()
                            )
                            client_connection.num = not client_connection.num

                    except socket.timeout:
                        send(
                            sock,
                            next_packet,
                            DEST_ADDR,
                            DEST_PORT,
                            packet_loss,
                            error_rate,
                        )
                complete_request = "".join(client_connection.receive_data_buffer)
                print(f"http request:\n{complete_request}")

                if complete_request[:3] == "GET":
                    file_name = complete_request.split(" ")[1].replace("/", "")
                    try:
                        f = open(file_name, "r")
                        status_code = 200
                        status = "OK"
                        file_content = f.read()
                    except FileNotFoundError:
                        print("File not found! Check the path variable and filename")
                        status_code = 404
                        status = "NOT FOUND"
                        file_content = ""
                    http_response = get_http_response(
                        "GET", status_code, status, file_content, server
                    )
                elif complete_request[:4] == "POST":
                    http_response = get_http_response("POST", 200, "OK", "", server)

                print(f"http response:\n{http_response}")
                client_connection.send_packets_buffer = get_packets(
                    http_response, client_connection.num
                )

                while len(client_connection.send_packets_buffer):
                    next_packet = client_connection.send_packets_buffer.pop(0)
                    send(
                        sock,
                        next_packet,
                        DEST_ADDR,
                        DEST_PORT,
                        packet_loss,
                        error_rate,
                    )
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
                                client_connection.num = not client_connection.num
                                break
                            else:
                                raise socket.timeout  # resend last packet
                        except socket.timeout:
                            send(
                                sock,
                                next_packet,
                                DEST_ADDR,
                                DEST_PORT,
                                packet_loss,
                                error_rate,
                            )

            else:
                print("Invalid request!")


def send(
    sock: socket.socket,
    packet,
    dest_addr,
    dest_port,
    packet_loss: float,
    error_rate: float,
) -> None:
    """_summary: emulates packet_loss and packet errors

    Args:
        sock: bound socket.
        packet: packet to be sent.
        dest_addr: address to send to.
        dest_port: port to send to.
        packet_loss (float): 0 to 1, indicates probability of packet loss.
        error_rate (float): 0 to 1, indicates probability of packet error.

    Returns:
        None
    """
    if packet_loss < 0 or packet_loss > 1:
        packet_loss = 0
    if error_rate < 0 or error_rate > 1:
        error_rate = 0
    p = random()
    if p >= packet_loss:  # don't lose packet
        p = random()
        if p < error_rate:  # do create error
            header = unpack(PACK_FORMAT, packet[:HEADER_LENGTH])
            checksum = header[0]
            packet = (
                pack(
                    PACK_FORMAT,
                    checksum + 1,  # corruption
                    header[1],
                    header[2],
                    header[3],
                    header[4],
                )
                + packet[HEADER_LENGTH:]
            )
        sock.sendto(packet, (dest_addr, dest_port))


def get_packets(http_request: str, last_num: bool) -> list:
    packets = []
    header_length = HEADER_LENGTH
    max_len_message = MAX_PACKET_SIZE - header_length
    n = ceil(len(http_request) / max_len_message)
    for i in range(n):
        message = http_request[:max_len_message]
        http_request = http_request[max_len_message:]
        num = last_num if (i % 2) == 0 else not last_num

        header = pack(
            PACK_FORMAT,
            0,
            num,
            0,  # ACK = 0
            0,  # FIN = 0
            (i != n - 1),  # 1 if MORE packets after this
        )
        packet = header + message.encode()
        checksum = crc32(packet)
        header = unpack(PACK_FORMAT, packet[:header_length])
        header = pack(
            PACK_FORMAT,
            checksum,
            header[1],
            header[2],
            header[3],
            header[4],
        )
        packet = header + packet[header_length:]
        packets.append(packet)
    return packets


def get_ack_packet(last_num: bool):
    header = pack(
        PACK_FORMAT,
        0,
        last_num,
        1,  # ACK = 1
        0,  # FIN = 0
        0,  # no more packets
    )
    checksum = crc32(header)
    header = pack(
        PACK_FORMAT,
        checksum,
        last_num,
        1,  # ACK = 1
        0,  # FIN = 0
        0,  # no more packets
    )
    return header
