from connection import ServerConnection
from messages import HandshakeMessage, BitfieldMessage, InterestedMessage,RequestMessage, UnchokeMessage, PieceMessage
from utils import parse_torrent_file_info, get_info_hash, recv_all
from constants import PIECE_SIZE, PROTOCOL_NAME, PEER_ID
from time import sleep
from messages import Message
import sys
import socket
from threading import Thread

def recv_handshake(conn):
    msg = recv_all(conn, 48 + len(PROTOCOL_NAME))
    conn.sendall(HandshakeMessage(PROTOCOL_NAME, get_info_hash('repo.torrent'), PEER_ID).encode())
    conn.sendall(BitfieldMessage(b'\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01').encode())

def receive_msg(conn):
    length = recv_all(conn,  3)
    print(length)
    length = int.from_bytes(length, 'big')
    if length == 0:
        return
    message = recv_all(conn,  length)
    print(message)
    message = Message.decode(message)
    if isinstance(message, InterestedMessage):
        conn.sendall(UnchokeMessage().encode())
    elif isinstance(message, RequestMessage):
        receive_request(conn, message)



def receive_request(conn, message):
    piece_index = message.index
    offset = message.begin
    length = message.length

    print(f"Received request for block {piece_index} offset {offset} length {length}")
    file_position = piece_index * PIECE_SIZE + offset

    files_info = parse_torrent_file_info('repo.torrent')
    
    while len(files_info) and file_position > files_info[0]['length']:
        file_position -= files_info[0]['length']
        files_info.pop(0)
    if len(files_info) == 0:
        return
    with open(files_info[0]['path'], 'rb') as f:
        f.seek(file_position)
        block = f.read(length)
        conn.sendall(PieceMessage(piece_index, offset, block).encode())

    print(f"Sent block {piece_index} offset {offset} length {length}")

def handle_connection(conn, addr):
    while True:
        first_byte = conn.recv(1)
        if first_byte == b'\x13':
            recv_handshake(conn)
            print("Handshake sent")
        else:
            print("Message received")
            receive_msg(conn)
    

def run(port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('localhost', port))
    server.listen()

    while True:
        conn, addr = server.accept()
        nconn = Thread(target=handle_connection, args=(conn,addr))
        nconn.start()


if __name__ == "__main__":
    run(int(sys.argv[1]))

