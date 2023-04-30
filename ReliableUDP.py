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
# MAX_PACKET_SIZE = 100
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
        client_connection = ClientConnectionInfo()

        while True:
            socket_error = False
            # SOCK_DGRAM is the socket type to use for UDP sockets
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind((SRC_ADDR, SRC_PORT))
            client_connection.num = 0
            client_connection.receive_data_buffer = []
            sock.settimeout(None)
            print("Server start...")
            packet, (DEST_ADDR, DEST_PORT) = sock.recvfrom(MAX_PACKET_SIZE)

            header = unpack(PACK_FORMAT, packet[:HEADER_LENGTH])
            print("Received packet header:", header)
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
                while more and not socket_error:
                    old_more = more
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
                        print("Received packet header:", header)
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
                        if crc32(packet) != checksum or fin:
                            print("Invalid checksum, or FIN; resending last packet.")
                            more = old_more
                            raise socket.timeout
                        elif num == client_connection.num:
                            if ack:
                                client_connection.num = not client_connection.num
                            else:
                                print("Invalid num; resending last packet.")
                                more = old_more
                                raise socket.timeout
                        else:
                            client_connection.receive_data_buffer.append(
                                packet[HEADER_LENGTH:].decode()
                            )
                            client_connection.num = not client_connection.num

                    except socket.timeout:
                        pass
                    except Exception as e:
                        print(e)
                        socket_error = True

                complete_request = "".join(client_connection.receive_data_buffer)
                print(f"\nhttp request:\n{complete_request}")

                if complete_request[:3] == "GET":
                    file_name = complete_request.split(" ")[1].replace("/", "")
                    try:
                        f = open(file_name, "r")
                        status_code = 200
                        status = "OK"
                        file_content = f.read()
                    except FileNotFoundError:
                        print("Requested file that was not found.")
                        status_code = 404
                        status = "NOT FOUND"
                        file_content = ""
                    http_response = get_http_response(
                        "GET", status_code, status, file_content, server
                    )
                elif complete_request[:4] == "POST":
                    http_response = get_http_response("POST", 200, "OK", "", server)

                print(f"\nhttp response:\n{http_response}")
                client_connection.send_packets_buffer = get_packets(
                    http_response, client_connection.num
                )

                max_tries = 10
                print(
                    f"** Sending {len(client_connection.send_packets_buffer)} packet(s)"
                )
                while len(client_connection.send_packets_buffer) and not socket_error:
                    next_packet = client_connection.send_packets_buffer.pop(0)
                    send(
                        sock,
                        next_packet,
                        DEST_ADDR,
                        DEST_PORT,
                        packet_loss,
                        error_rate,
                    )

                    while not socket_error:
                        try:
                            packet, (addr, port) = sock.recvfrom(MAX_PACKET_SIZE)
                            # check not corrupted
                            header = unpack(PACK_FORMAT, packet[:HEADER_LENGTH])
                            print("Received packet header:", header)
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
                                    print(
                                        "Invalid num, or not ACK, or FIN; resending last packet."
                                    )
                                    raise socket.timeout
                                client_connection.num = not client_connection.num
                                break
                            else:
                                print("Invalid checksum; resending last packet.")
                                raise socket.timeout  # resend last packet
                        except socket.timeout:
                            if len(client_connection.send_packets_buffer) == 0:
                                if max_tries == 0:
                                    print(
                                        "Reached max tries for last packet; ending connection."
                                    )
                                    break
                                max_tries -= 1
                            send(
                                sock,
                                next_packet,
                                DEST_ADDR,
                                DEST_PORT,
                                packet_loss,
                                error_rate,
                            )
                        except Exception as e:
                            print(e)
                            socket_error = True
            else:
                print("Invalid checksum, or invalid num, or ACK, or FIN.")
            try:
                sock.shutdown(socket.SHUT_RDWR)
                sock.close()
            except Exception as e:
                print(e)


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
            print("Packet corrupted.")
        header = unpack(PACK_FORMAT, packet[:HEADER_LENGTH])
        print("Sent packet header:", header)
        sock.sendto(packet, (dest_addr, dest_port))
        print("Packet sent.")
    else:
        print("Packet lost.")


def get_packets(http_request: str, last_num: bool) -> list:
    packets = []
    header_length = HEADER_LENGTH
    max_len_message = MAX_PACKET_SIZE - header_length
    n = ceil(len(http_request) / max_len_message)
    for i in range(n):
        message = http_request[:max_len_message]
        http_request = http_request[max_len_message:]
        if i % 2 == 0:
            num = last_num
        else:
            num = not last_num

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
