import socket
from zlib import crc32
from ReliableUDP import *
from http10 import *

SRC_ADDR, SRC_PORT = "localhost", 9999
server = "apache 2.0"
# SOCK_DGRAM is the socket type to use for UDP sockets
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((SRC_ADDR, SRC_PORT))
client_connection = ClientConnectionInfo()

while True:
    client_connection.receive_data_buffer = []
    sock.settimeout(None)
    print("Server start")
    packet, (DEST_ADDR, DEST_PORT) = sock.recvfrom(MAX_PACKET_SIZE)
    print("Received first packet")
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
        print("Valid packet")
        client_connection.receive_data_buffer.append(packet[HEADER_LENGTH:].decode())
        sock.settimeout(PACKET_LOSS_TIMEOUT)
        print ("i got this :",client_connection.receive_data_buffer)
        more = 1
        while more:
            print("iam in more loop")
            try:
                print("iam in try in more loop")
                response_packet = get_ack_packet(client_connection.num)
                print("iam in try in more loop1")
                sock.sendto(response_packet, (DEST_ADDR, DEST_PORT))
                print("iam in try in more loop2")
                packet, (DEST_ADDR, DEST_PORT) = sock.recvfrom(MAX_PACKET_SIZE)
                print("iam in try in more loop3")
                header = unpack(PACK_FORMAT, packet[:HEADER_LENGTH])
                checksum = header[0]
                num = header[1]
                ack = header[2]
                fin = header[3]
                more = header[4]
                print("num: ", num, "client_connection.num ", client_connection.num)
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
                sock.sendto(response_packet, (DEST_ADDR, DEST_PORT))
        complete_request = "".join(client_connection.receive_data_buffer)
        print("this is the complete re:",complete_request)

        
        if complete_request[:3] == "GET":
            file_name = complete_request.split(" ")[1].replace("/", "")
            try:
                f = open(file_name, "r")
                status_code = 200
                status = "OK"
                file_content = f.read()
            except FileNotFoundError:
                print("File not found. Check the path variable and filename")
                status_code = 404
                status = "NOT FOUND"
                file_content = ""
            http_response = get_http_response(
                "GET", status_code, status, file_content, server
            )
            client_connection.send_packets_buffer = get_packets(
                http_response, client_connection.num
            )
            while len(client_connection.send_packets_buffer):
                next_packet = client_connection.send_packets_buffer.pop(0)
                sock.sendto(next_packet, (DEST_ADDR, DEST_PORT))
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
                        else:
                            raise socket.timeout  # resend last packet
                    except socket.timeout:
                        sock.sendto(next_packet, (DEST_ADDR, DEST_PORT))
        elif complete_request[:4] == "POST":
            http_response = get_http_response("POST", 200, "OK", "", server)
            client_connection.send_packets_buffer = get_packets(
                http_response, client_connection.num
            )
            print ("should send:",http_response)
            print("***send_packets_buffer my len is: ",len(client_connection.send_packets_buffer))
            while len(client_connection.send_packets_buffer):
                next_packet = client_connection.send_packets_buffer.pop(0)
                sock.sendto(next_packet, (DEST_ADDR, DEST_PORT))
                while True:
                    
                    try:
                        packet, (addr, port) = sock.recvfrom(MAX_PACKET_SIZE)
                        # check not corrupted
                        header = unpack(PACK_FORMAT, packet[:HEADER_LENGTH])
                        checksum = header[0]
                        num = header[1]
                        ack = header[2]
                        fin = header[3]
                        print("num: ", num, "client_connection.num ", client_connection.num)
                        
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
                        print("client_connection.num ",client_connection.num)
                        if crc32(packet) == checksum:
                            if num != client_connection.num or not ack or fin:
                                raise socket.timeout
                            client_connection.num = not client_connection.num
                            break
                        else:
                            raise socket.timeout  # resend last packet
                    except socket.timeout:
                        sock.sendto(next_packet, (DEST_ADDR, DEST_PORT))
            print ("I am done")
            print(complete_request)
        else:
            print("Invalid request!")
