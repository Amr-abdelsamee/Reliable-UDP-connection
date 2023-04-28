import socketserver
from ReliableUDP import *


class ReliableUDPHandler(socketserver.BaseRequestHandler):
    clients_connections: dict[str, ClientConnectionInfo] = {}

    def __init__(
        self,
        request,
        client_address,
        server,
        clients_connections,
    ) -> None:
        super().__init__(request, client_address, server)
        self.clients_connections = clients_connections

    def handle(self):
        if self.client_address == None:  # deal with timeout(s)
            current_datetime = datetime.now()
            current_datetime_iso = current_datetime.isoformat(timespec="microseconds")
            for client_connection in self.clients_connections:
                # find out which client(s) timed out and deal with them
                pass
        else:
            if self.client_address in self.clients_connections:
                # continue client connection
                pass
            else:
                # new client connection
                pass
            # dummy code start
            data = self.request[0].strip()
            socket = self.request[1]
            print("{} wrote:".format(self.client_address[0]))
            print(data)
            socket.sendto(data.upper(), self.client_address)
            # dummy code end
        return self.clients_connections


if __name__ == "__main__":
    HOST, PORT = "localhost", 9999
    with ReliableUDPServer((HOST, PORT), ReliableUDPHandler, {}) as server:
        server.serve_forever()
