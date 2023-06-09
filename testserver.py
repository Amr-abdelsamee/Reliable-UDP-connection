import socketserver
from ReliableUDP import *


class ReliableUDPHandler(socketserver.BaseRequestHandler):
    clients_connections: dict[str, ClientConnectionInfo] = {}

    def __init__(
        self,
        request,
        client_address,
        client_port,
        server: ReliableUDPServer,
        clients_connections: dict[str, ClientConnectionInfo],
    ) -> dict[str, ClientConnectionInfo]:
        super().__init__(request, client_address, server)
        self.clients_connections = clients_connections
        if client_address != None:
            self.packet = self.request[0]
            self.socket = self.request[1]
            self.client_port = client_port

    def handle(self) -> dict[str, ClientConnectionInfo]:
        if self.client_address == None:  # deal with timeout(s)
            current_datetime = datetime.now()
            current_datetime_iso = current_datetime.isoformat(timespec="microseconds")
            for client_addr, client_connection in self.clients_connections.items():
                if client_connection.waiting:
                    # find out which client(s) timed out and deal with them
                    client_datetime = datetime.fromisoformat(
                        client_connection.datetime_iso
                    )
                    if (
                        current_datetime - client_datetime
                    ).total_seconds() >= self.server.packet_loss_timeout:
                        self.socket.sendto(
                            client_connection.last_packet,
                            (client_addr, self.client_port),
                        )
                        self.clients_connections[
                            client_addr
                        ].datetime_iso = current_datetime_iso
        else:
            # check not corrupted
            header = unpack(self.packet[:HEADER_LENGTH])
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
                    header[5],
                )
                + packet[HEADER_LENGTH:]
            )
            if crc32(packet) == checksum:
                if self.client_address in self.clients_connections:
                    client_connection = self.clients_connections[self.client_address]
                    if num != client_connection.num:
                        self.socket.sendto(
                            client_connection.last_packet,
                            (self.client_address, self.client_port),
                        )
                        current_datetime = datetime.now()
                        current_datetime_iso = current_datetime.isoformat(
                            timespec="microseconds"
                        )
                        self.clients_connections[
                            self.client_address
                        ].datetime_iso = current_datetime_iso
                    else:
                        if fin and ack:  # FIN & ACK connection closed
                            self.clients_connections.pop(self.client_address)
                        elif fin:  # FIN
                            packet = get_fin_packet(
                                client_connection.num,
                                1,
                            )
                            self.socket.sendto(
                                packet,
                                (self.client_address, self.client_port),
                            )
                            current_datetime = datetime.now()
                            current_datetime_iso = current_datetime.isoformat(
                                timespec="microseconds"
                            )
                            self.clients_connections[
                                self.client_address
                            ].datetime_iso = current_datetime_iso
                            self.clients_connections[
                                self.client_address
                            ].last_packet = packet
                            self.clients_connections[self.client_address].waiting = 1
                        else:
                            # TODO: parse http
                            # server maybe will need while loop here to finish sending the whole file
                            # or receive part of file
                            # continue client connection
                            pass
                else:
                    # new client connection
                    if num == 0:  # num should start with 0, otherwise ignore
                        self.clients_connections[
                            self.client_address
                        ] = ClientConnectionInfo()
                        data = packet[HEADER_LENGTH:].decode()

                        if data[:3] == "GET":
                            client_connection.GET = 1
                            client_connection.working = 1
                            client_connection.receive_data_buffer.append(data)
                            if more:
                                response_packet = get_ack_packet(num)
                                self.socket.sendto(
                                    response_packet,
                                    (self.client_address, self.client_port),
                                )
                            else:
                                # get file into packets
                                # add to send_data_buffer
                                # start sending
                                # start sending response
                                pass
                        else:
                            

                        # TODO: parse http
                        # server maybe will need while loop here to finish sending the whole file
                        # or receive part of file
                        # continue client connection
                else:
                client_connection = self.clients_connections[self.client_address]
                self.socket.sendto(
                    client_connection.last_packet,
                    (self.client_address, self.client_port),
                )
                current_datetime = datetime.now()
                current_datetime_iso = current_datetime.isoformat(
                    timespec="microseconds"
                )
                self.clients_connections[
                    self.client_address
                ].datetime_iso = current_datetime_iso
        return self.clients_connections


if __name__ == "__main__":
    HOST, PORT = "localhost", 9999
    with ReliableUDPServer((HOST, PORT), ReliableUDPHandler) as server:
        server.serve_forever()
