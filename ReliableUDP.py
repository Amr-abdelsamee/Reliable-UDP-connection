import socket
from datetime import datetime
from struct import pack, unpack
from zlib import crc32
from math import ceil

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
    datetime_iso: str = ""  # datetime_iso of last packet sent
    send_packets_buffer: list[str] = []
    receive_data_buffer: list[str] = []
    working: bool = 0
    GET: bool = 1  # 1 == GET, 0 == POST
    last_packet: str = ""  # holds the last packet sent incase it needs to be resent


class ReliableUDPServer:
    max_packet_size: int = MAX_PACKET_SIZE
    packet_loss_timeout: float = PACKET_LOSS_TIMEOUT  # packet_loss_timeout in seconds
    clients_connections: dict[str, ClientConnectionInfo] = {}
    # maps each client address (str) to their own ClientConnectionInfo

    def __init__(
        self,
        server_address,
        RequestHandlerClass,
    ):
        self.server_address = server_address
        self.RequestHandlerClass = RequestHandlerClass
        self.socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM
        )  # create UDP socket
        self.server_bind()

    def server_bind(self):
        self.socket.bind(self.server_address)
        self.server_address = self.socket.getsockname()

    def serve_forever(self):
        while True:
            try:
                self.data, (self.client_addr, self.client_port) = self.socket.recvfrom(
                    self.max_packet_size
                )
            except socket.timeout:
                # set client addr to None, so RequestHandlerClass knows it's a timeout
                self.client_addr = None
                pass
            finally:
                self.clients_connections: dict[
                    str, ClientConnectionInfo
                ] = self.RequestHandlerClass(
                    (self.data, self.socket),
                    self.client_addr,
                    self.client_port,
                    self,
                    self.clients_connections,
                    self.packet_loss_timeout,
                )

            current_datetime = datetime.now()
            current_datetime_iso = current_datetime.isoformat(timespec="microseconds")
            min_datetime_iso = current_datetime_iso
            for _, client_connection in self.clients_connections.items():
                if client_connection.SENT:
                    min_datetime_iso = min(
                        min_datetime_iso, client_connection.datetime_iso
                    )
            # calculate the minimum timeout to ensure the closest expiry is checked
            min_datetime = datetime.fromisoformat(min_datetime_iso)
            min_timeout = max(
                0,
                self.packet_loss_timeout
                - (current_datetime - min_datetime).total_seconds(),
            )

            self.socket.settimeout(min_timeout)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def get_packets(http_request: str, last_num: bool) -> list:
    packets = []
    header_length = HEADER_LENGTH
    max_len_message = MAX_PACKET_SIZE - header_length
    n = ceil(len(http_request) / max_len_message)
    for i in range(n):
        message = http_request[:max_len_message]
        http_request = http_request[max_len_message:]
        num = last_num if (i % 2) == 0 else not last_num
        print(num)
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


def get_fin_packet(last_num: bool, ack: bool):
    header = pack(
        PACK_FORMAT,
        0,
        last_num,
        ack,
        1,  # FIN = 1
        0,  # no more packets
    )
    checksum = crc32(header)
    header = pack(
        PACK_FORMAT,
        checksum,
        last_num,
        ack,
        1,  # FIN = 1
        0,  # no more packets
    )
    return header
