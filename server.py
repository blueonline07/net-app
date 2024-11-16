from messages import HandshakeMessage, BitfieldMessage, InterestedMessage,RequestMessage, UnchokeMessage, PieceMessage, Message
from utils import parse_torrent_file_info, get_info_hash, recv_all, get_bitfield
from constants import PIECE_SIZE, PROTOCOL_NAME, PEER_ID, PEER_PORT
import socket
from threading import Thread
from torrent import Torrent

dir_name = 'downloads'

def receive_handshake(conn):
    msg = recv_all(conn, 48 + len(PROTOCOL_NAME))
    handshake_rcv = Message.decode(b'\x13' + msg)
    if handshake_rcv.info_hash != get_info_hash(dir_name + '.torrent'):
        print("Invalid info hash")
        conn.sendall(0xFF)
        conn.close()
    else:
        conn.sendall(b'\x00') #send anything not 0xFF
    conn.sendall(HandshakeMessage(PROTOCOL_NAME, get_info_hash(dir_name + '.torrent'), PEER_ID).encode())
    bitfield = get_bitfield(dir_name + '.torrent')
    conn.sendall(BitfieldMessage(bitfield).encode())


def receive_request(conn, message): #send the block requested
    piece_index = message.index
    offset = message.begin
    length = message.length

    # print(f"Received request for piece {piece_index} offset {offset} length {length}")
    file_position = piece_index * PIECE_SIZE + offset
    files_info = parse_torrent_file_info(dir_name + '.torrent')
    
    while len(files_info) and file_position > files_info[0]['length']:
        file_position -= files_info[0]['length']
        files_info.pop(0)
    if len(files_info) == 0:
        conn.sendall(b'\x00\x00\x00\x00')
        return
    
    if file_position + length > files_info[0]['length']:
        try:
            with open(files_info[0]['path'], 'rb') as f:
                f.seek(file_position)
                block = f.read(files_info[0]['length'] - file_position)
            if len(files_info) > 1:
                with open(files_info[1]['path'], 'rb') as f:
                    block += f.read(length - len(block))
        except FileNotFoundError:
            block = b''

        
    else:
        try:
            with open(files_info[0]['path'], 'rb') as f:
                f.seek(file_position)
                block = f.read(length)
        except FileNotFoundError:
            block = b''
    conn.sendall(PieceMessage(piece_index, offset, block).encode())
    # print(f"Sent piece {piece_index} offset {offset} length {length}")

def handle_connection(conn, addr):
    while True:
        first_byte = conn.recv(1)
        if first_byte == b'\x13':
            receive_handshake(conn)
        elif first_byte == b'\x00':
            length = int.from_bytes(recv_all(conn, 3), 'big')
            msg = Message.decode(recv_all(conn, length)) 
            if isinstance(msg, RequestMessage):
                receive_request(conn, msg)
        

        elif first_byte == b'':
            print("Connection closed")
            conn.close()
            break


class Server:
    def __init__(self,torrent_file_name, port):
        self.torrent = Torrent.from_torrent_file(torrent_file_name)
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.bitfield = get_bitfield(torrent_file_name)

        
    def start(self):
        self.server.bind(('0.0.0.0', self.port))
        self.server.listen(5)
        print(f"Server started on {socket.gethostbyname(socket.gethostname())}:{self.port}")
        while True:
            conn, addr = self.server.accept()
            print(f"Connection from {addr}")
            nconn = Thread(target=handle_connection, args=(conn,addr))
            nconn.start()
