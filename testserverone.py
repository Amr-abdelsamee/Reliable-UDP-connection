from ReliableUDP import ReliableUDPServer

PACKET_LOSS = 0.3
ERROR_RATE = 0.3

reliable_udp_server = ReliableUDPServer()
reliable_udp_server.serve_forever(PACKET_LOSS, ERROR_RATE)
