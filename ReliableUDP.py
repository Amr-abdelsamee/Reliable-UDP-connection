import socket
from datetime import datetime


class ClientConnectionInfo:
    last_ack: int = 0
    last_ack_datetime_iso: str = ""
    last_seq: int = 0
    last_seq_datetime_iso: str = ""
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
            for client_connection in self.clients_connections:
                min_datetime_iso = min(
                    min_datetime_iso, client_connection.last_ack_timestamp
                )
                min_datetime_iso = min(
                    min_datetime_iso, client_connection.last_seq_timestamp
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
