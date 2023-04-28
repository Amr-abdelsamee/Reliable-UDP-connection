import socket
from datetime import datetime
from struct import pack
from zlib import crc32


class ClientConnectionInfo:
    ack: int = 0
    seq: int = 1
    datetime_iso: str = ""
    packets_buffer: list[str] = []
    control_flag_bits: int = 0b000000


class ReliableUDPServer:
    max_packet_size: int = 8192
    packet_loss_timeout: float = 0.3  # packet_loss_timeout in seconds
    clients_connections: dict[str, ClientConnectionInfo] = {}
    # maps each client address (str) to their own ClientConnectionInfo

    def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True):
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
                self.data, self.client_addr = self.socket.recvfrom(self.max_packet_size)
            except socket.timeout:
                # set client addr to None, so RequestHandlerClass knows it's a timeout
                self.client_addr = None
                pass
            finally:
                self.clients_connections = self.RequestHandlerClass(
                    (self.data, self.socket),
                    self.client_addr,
                    self,
                    self.clients_connections,
                )

            current_datetime = datetime.now()
            current_datetime_iso = current_datetime.isoformat(timespec="microseconds")
            min_datetime_iso = current_datetime_iso
            for _, client_connection in self.clients_connections:
                min_datetime_iso = min(min_datetime_iso, client_connection.datetime_iso)
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


class ReliableUDPClient:
    max_packet_size: int = 8192
    packet_loss_timeout: float = 0.3  # packet_loss_timeout in seconds
    client_connection: ClientConnectionInfo

    def wrap_http(
        self, method: str, file_name: str, data: str, host: str, user_agent: str
    ) -> str:
        message = f"""{method} /{file_name} HTTP/1.0
        Host: {host}
        User-Agent: {user_agent}"""
        if method == "POST":
            message += f"""
            Content-Type: text/html
            Content-Length: {len(data)}"""
        return message

    def get_packets(self, http_request: str) -> list:
        packets = []
        header_length = (
            20  # 4 byte unsigned int [ack, seq, control_flag_bits, checksum]
        )
        max_len = self.max_packet_size - header_length
        n = len(http_request) / max_len
        for i in range(n):
            message = http_request[:max_len]
            checksum = crc32(message)
            http_request = http_request[max_len:]
            packet = pack(
                f"!IIIII{len(message)}s",
                self.client_connection.ack,
                self.client_connection.seq,
                self.client_connection.control_flag_bits,
                checksum,
                message,
            )
            packet_len = header_length + len(message)
            self.client_connection.seq += packet_len

            packets.append(packet)

        return packets


"""


"""
