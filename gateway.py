import socket
from datetime import datetime
from ReliableUDP import get_packets
from http10 import *
from ReliableUDP import *
TCP_SRC_PORT = 3030
UDP_SRC_PORT = 7777
DEST_PORT = 9999
HOST = 'localhost'
user_agent = (
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1"
)

def udp_connection(http_request):
    print ("-------------------------------")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, UDP_SRC_PORT))
    method = http_request[:4]

    
    if method == "POST":
        http_request = get_http_request("POST", "", http_request.split("\r\n\r\n")[1],f"{HOST}:{DEST_PORT}", user_agent)
    else:
        http_request = get_http_request("GET", http_request.split(" ")[1][1:], "",f"{HOST}:{DEST_PORT}", user_agent)

    client_connection = ClientConnectionInfo()
    client_connection.send_packets_buffer = get_packets(http_request, 0)

    while len(client_connection.send_packets_buffer):
        next_packet = client_connection.send_packets_buffer.pop(0)
        sock.sendto(next_packet, (HOST, DEST_PORT))
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
                    client_connection.receive_data_buffer.append(packet)
                    client_connection.num = not client_connection.num
                    break
                else:
                    raise socket.timeout  # resend last packet
            except socket.timeout:
                sock.sendto(next_packet, (HOST, DEST_PORT))
    
    next_packet = get_ack_packet(not client_connection.num)
    sock.sendto(next_packet, (HOST, DEST_PORT))



    client_connection.receive_data_buffer = []
    more = 1
    while more:
        try:
            packet, (addr, port) = sock.recvfrom(MAX_PACKET_SIZE)
            # check not corrupted
            header = unpack(PACK_FORMAT, packet[:HEADER_LENGTH])
            checksum = header[0]
            num = header[1]
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
            if crc32(packet) == checksum:
                if num != client_connection.num or fin:
                    raise socket.timeout
                client_connection.receive_data_buffer.append(
                    packet[HEADER_LENGTH:].decode()
                )
                next_packet = get_ack_packet(client_connection.num)
                client_connection.num = not client_connection.num
                sock.sendto(next_packet, (HOST, DEST_PORT))
                
            else:
                raise socket.timeout
        except socket.timeout:
            sock.sendto(next_packet, (HOST, DEST_PORT))


    http_response = "".join(client_connection.receive_data_buffer)
    print("http response:: \n"+http_response)


    sock.sendto(http_request.encode(), (HOST, DEST_PORT))
    sock.close()




while(True):
    TCP_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    TCP_server.bind((HOST, TCP_SRC_PORT))

    TCP_server.listen(1)
    print(" :: Listening on port ",TCP_SRC_PORT)

    connection, rec_adrs = TCP_server.accept()
    print(" :: Connection established with:", rec_adrs)

    rec_message = connection.recv(TCP_SRC_PORT).decode()

    print(datetime.now().strftime("%H:%M:%S") + " :: Recieved message:\n", rec_message)
    


    connection.close()
    TCP_server.close()
    udp_connection(rec_message)



